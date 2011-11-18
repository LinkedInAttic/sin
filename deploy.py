#!/usr/bin/env python
import getpass, logging, os, re, signal, sys, time, urllib
from optparse import OptionParser

SIN_HOME = os.path.normpath(os.path.join(os.path.normpath(__file__), '..'))

APP_HOME = os.path.join(SIN_HOME, 'app')

app_settings = 'settings'
app_path = APP_HOME

os.environ['DJANGO_SETTINGS_MODULE'] = app_settings
if app_path:
  sys.path.insert(0, app_path)

from django.conf import settings

try:
  import paramiko
except ImportError:
  print "paramiko is not installed. Please go to http://www.lag.net/paramiko/"
  print "download the latest package, untar, cd into that directory, and run"
  print "sudo easy_install ./"
  sys.exit(1)

global_pass = ''

class BaseDeployer(object):
  def __init__(self, host, home, node_id, login=None, server=False, user='root', upgrade=False, base=None):
    global global_pass

    self.host    = host
    self.home    = home
    self.node_id = node_id
    self.login   = login
    self.server  = server
    self.user    = user
    self.upgrade = upgrade
    self.base    = base

    self.password  = None
    self.pass_sent = False

    if base:
      self.ssh   = base.ssh
      self.sftp  = base.sftp
      self.shell = base.shell
    else:
      self.ssh = paramiko.SSHClient()
      self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
      retry = 0
      while True:
        try:
          self.ssh.connect(self.host, username=self.login, password=self.password)
          break
        except paramiko.AuthenticationException:
          retry += 1
          if retry > 3:
            print "Authentication failed."
            sys.exit(1)
          self.password = global_pass = getpass.getpass()
      self.sftp  = self.ssh.open_sftp()
      self.shell = self.ssh.invoke_shell()

      # Read welcome message:
      self._read_data()
      print self.command('sudo -u %s sh' % 'root')

  def get_deployer(self):
    data = self.command('uname -a')
    print data
    if 'el6.x86_64' in data:
      deployer_class = DeployerRHEL6_X86_64
    elif 'Darwin' in data:
      if 'x86_64' in data:
        deployer_class = DeployerDarwin_X86_64
      elif 'i386' in data:
        deployer_class = DeployerDarwin_I386
    else:
      print 'Platform not supported. You may have to install manually by'
      print 'following: http://linkedin.jira.com/wiki/display/SIN/Developer+Setup'
      sys.exit(1)

    return deployer_class(self.host,
                          self.home,
                          self.node_id,
                          login   = self.login,
                          server  = self.server,
                          user    = self.user,
                          upgrade = self.upgrade,
                          base    = self)

  def _check_sudo(self, data):
    global global_pass
    lines = re.split(r'[\r\n]+', data)
    promot = lines[-1]
    if re.match(r'^\[sudo\] password for \w+: $', promot):
      # Need password
      if self.pass_sent:
        if data:
          print data
          data = ''
        self.password = global_pass = getpass.getpass()

      if not self.password:
        if not global_pass:
          if data:
            print data
            data = ''
          self.password = global_pass = getpass.getpass()
        else:
          self.password = global_pass

      self.pass_sent = True
      self.shell.send('%s\n' % self.password)
    else:
      if self.pass_sent:
        if re.match(r'^[#\$] $', promot[-2:]): # Looking for shell promot '$ ' or '# '.
          if len(lines) > 1:
            if re.match(r'sudo: \d+ incorrect password attempts', lines[-2]):
              # Wrong password
              self.password = global_pass = ''
              raise Exception(lines[-2])
          self.pass_sent = False

    return data

  def _read_data(self):
    d = ''
    while not re.match(r'^[#\$] $', d[-2:]):  # Looking for shell promot '$ ' or '# '.
      while not self.shell.recv_ready():
        time.sleep(.1)
      d += self.shell.recv(8192)
      d = self._check_sudo(d)

    return d

  def command(self, cmd):
    self.shell.send('%s 2>&1\n' % cmd)
    return self._read_data()

  def get_python_version(self):
    data = self.command('python --version')
    version = None
    m = re.search(r'(?m)^Python (?P<version>[\d\.]+)', data)
    if m:
      version = m.group('version')

    if version:
      return version.split('.')

    return None

  def autostart(self, service, on=True):
    raise Exception("Not implemented")

  def check_zkpython(self):
    data = self.command('python -c "import zookeeper"')
    print data
    if 'ImportError:' in data:
      return False
    return True

  def install_zkpython(self):
    if self.check_zkpython():
      return

    self.do_install_zkpython()

  def do_install_zkpython(self):
    raise Exception("Not implemented")

  def check_setuptools(self):
    data = self.command('easy_install --version')
    print data
    if 'command not found' in data:
      return False
    return True

  def install_setuptools(self):
    if self.check_setuptools():
      return

    self.do_install_setuptools()

  def do_install_setuptools(self):
    print 'Installing setuptools...'
    py_version = self.get_python_version()
    tmpfile = 'setuptools-0.6c11-py%s.%s.egg' % (py_version[0], py_version[1])
    tmpfile_local = os.path.expanduser('~/local-%s' % tmpfile)
    if not os.path.exists(tmpfile_local):
      urllib.urlretrieve('http://pypi.python.org/packages/%s.%s/s/setuptools/%s' % (py_version[0],
                                                                                    py_version[1],
                                                                                    tmpfile), tmpfile_local)
    try: self.sftp.remove(tmpfile)
    except: pass

    self.sftp.put(tmpfile_local, tmpfile)

    print self.command('sh %s' % tmpfile)

    try: self.sftp.remove(tmpfile)
    except: pass

    if not self.check_setuptools():
      raise Exception("setuptools install failed!")
    print 'setuptools installed.'

  def check_django(self):
    data = self.command('python -c "import django"')
    print data
    if 'ImportError:' in data:
      return False
    return True

  def install_django(self):
    if self.check_django():
      return

    print 'Installing django...'
    version = '1.3.1'
    name = 'Django-%s' % version
    tmpfile = '%s.tar.gz' % name
    tmpfile_local = os.path.expanduser('~/local-%s' % tmpfile)
    if not os.path.exists(tmpfile_local):
      urllib.urlretrieve('http://www.djangoproject.com/download/%s/tarball/' % version, tmpfile_local)

    try: self.sftp.remove(tmpfile)
    except: pass
    self.command('\\rm -Rf %s' % name)  # Remove the tmp dir

    self.sftp.put(tmpfile_local, tmpfile)

    self.command('tar xzf %s' % tmpfile)
    print self.command('python %s/setup.py install' % name)

    self.command('\\rm -Rf %s' % name)  # Remove the tmp dir
    try: self.sftp.remove(tmpfile)
    except: pass
    # Local file are not removed.

    if not self.check_django():
      raise Exception("django install failed!")
    print 'django installed.'

  def check_twisted(self):
    data = self.command('python -c "import twisted.web"')
    print data
    if 'ImportError:' in data:
      return False
    return True

  def install_twisted(self):
    if self.check_twisted():
      return

    self.do_install_twisted()

  def do_install_twisted(self):
    print 'Installing twisted...'
    print self.command('easy_install Twisted')
    if not self.check_twisted():
      raise Exception("twisted install failed!")
    print 'twisted installed.'

  def check_cronolog(self):
    data = self.command('cronolog --version')
    print data
    if 'command not found' in data:
      return False
    return True

  def install_cronolog(self):
    if self.check_cronolog():
      return

    self.do_install_cronolog()

  def do_install_cronolog(self):
    raise Exception("Not implemented")

  def check_pyparsing(self):
    data = self.command('python -c "import pyparsing"')
    print data
    if 'ImportError:' in data:
      return False
    return True

  def install_pyparsing(self):
    if self.check_pyparsing():
      return

    print 'Installing pyparsing...'
    version = '1.5.5'
    name = 'pyparsing-%s' % version
    tmpfile = '%s.tar.gz' % name
    tmpfile_local = os.path.expanduser('~/local-%s' % tmpfile)
    if not os.path.exists(tmpfile_local):
      urllib.urlretrieve('http://cheeseshop.python.org/packages/source/p/pypar'
                         'sing/pyparsing-%s.tar.gz' % version, tmpfile_local)

    try: self.sftp.remove(tmpfile)
    except: pass
    self.command('\\rm -Rf %s' % name)  # Remove the tmp dir

    self.sftp.put(tmpfile_local, tmpfile)

    self.command('tar xzf %s' % tmpfile)
    print self.command('easy_install %s' % name)

    self.command('\\rm -Rf %s' % name)  # Remove the tmp dir
    try: self.sftp.remove(tmpfile)
    except: pass
    # Local file are not removed.

    if not self.check_pyparsing():
      raise Exception("pyparsing install failed!")
    print 'pyparsing installed.'

  def check_pysensei(self):
    data = self.command('python -c "import sensei"')
    print data
    if 'ImportError:' in data:
      return False
    return True

  def install_pysensei(self):
    if self.check_pysensei():
      return

    print 'Installing sensei-python...'
    version = '1.0'
    name = 'sensei-python-%s' % version
    tmpfile = '%s.tar.gz' % name
    tmpfile_local = os.path.expanduser('~/local-%s' % tmpfile)
    if not os.path.exists(tmpfile_local):
      urllib.urlretrieve('https://github.com/downloads/javasoze/sensei/sensei-'
                         'python-%s.tar.gz' % version, tmpfile_local)

    try: self.sftp.remove(tmpfile)
    except: pass
    self.command('\\rm -Rf %s' % name)  # Remove the tmp dir

    self.sftp.put(tmpfile_local, tmpfile)

    self.command('tar xzf %s' % tmpfile)
    print self.command('easy_install %s' % name)

    self.command('\\rm -Rf %s' % name)  # Remove the tmp dir
    try: self.sftp.remove(tmpfile)
    except: pass
    # Local file are not removed.

    if not self.check_pysensei():
      raise Exception("sensei-python install failed!")
    print 'sensei-python installed.'

  def check_sin(self):
    sin_server = '/etc/init.d/sin_server'
    data = self.command('ls %s' % sin_server)
    print data
    if 'No such file or directory' in data:
      return False
    return True

  def install_sin(self):
    if not self.upgrade and self.check_sin():
      return

    print 'Installing sin...'
    tmpfile = 'sin.tar.gz'
    tmpfile_local = os.path.expanduser('~/local-%s' % tmpfile)
    # Packaging:
    os.system('tar -C %s -czf %s --exclude log --exclude app/django --exclude '
              'demo/django --exclude admin/um --exclude "*.swp" --exclude "*.pyc" ./' % (SIN_HOME, tmpfile_local))

    sin_server = '/etc/init.d/sin_server'
    sin_agent = '/etc/init.d/sin_agent'
    tmp_sin_server = 'sin_server'
    tmp_sin_agent = 'sin_agent'

    sin_server_src = 'start_script/linux/sin_server'
    sin_agent_src = 'start_script/linux/sin_agent'
    f = open(os.path.join(SIN_HOME, sin_server_src))
    server = f.read()
    f.close()
    f = open(os.path.join(SIN_HOME, sin_agent_src))
    agent = f.read()
    f.close()

    server = re.sub(r'(?m)^HOME=.*$', 'HOME=%s' % self.home, server)
    server = re.sub(r'(?m)^USER=.*$', 'USER=%s' % self.user, server)
    agent = re.sub(r'(?m)^HOME=.*$', 'HOME=%s' % self.home, agent)
    agent = re.sub(r'(?m)^USER=.*$', 'USER=%s' % self.user, agent)
    agent = re.sub(r'(?m)^NODE_ID=.*$', 'NODE_ID=%s' % self.node_id, agent)

    # Install:
    try: self.sftp.remove(tmpfile)
    except: pass
    try: self.sftp.remove(tmp_sin_server)
    except: pass
    try: self.sftp.remove(tmp_sin_agent)
    except: pass

    self.sftp.put(tmpfile_local, tmpfile)

    f = self.sftp.file(tmp_sin_server, 'w')
    f.write(server)
    f.flush()
    f.close()

    f = self.sftp.file(tmp_sin_agent, 'w')
    f.write(agent)
    f.flush()
    f.close()
    print self.command('chmod 755 %s' % tmp_sin_server)
    print self.command('chmod 755 %s' % tmp_sin_agent)

    # Find out the default group the run as user in:
    data = self.command('groups %s' % self.user)
    group = None
    m = re.search(r'(?m)^\S+ : (?P<group>\S+).*$', data)
    if m:
      group = m.group('group')

    if self.upgrade:
      self.autostart('sin_server', off)
      self.autostart('sin_agent', off)
      print self.command('%s stop' % sin_server)
      print self.command('%s stop' % sin_agent)

    print self.command('mkdir -p %s' % os.path.join(self.home, 'log/sin_server'))
    print self.command('mkdir -p %s' % os.path.join(self.home, 'log/sin_agent'))
    print self.command('tar -C %s -xzf %s' % (self.home, tmpfile))

    print self.command('\\cp -f %s %s' % (tmp_sin_server, os.path.join(self.home, sin_server_src)))
    data = self.command('\\cp -f %s %s' % (tmp_sin_agent, os.path.join(self.home, sin_agent_src)))
    if not 'No such file or directory' in data:
      if group:
        print self.command('chown -R %s:%s %s' % (self.user, group, self.home))
      else:
        print self.command('chown -R %s %s' % (self.user, self.home))

      print self.command('\\cp -f %s %s' % (tmp_sin_server, sin_server))
      print self.command('\\cp -f %s %s' % (tmp_sin_agent, sin_agent))

      if self.server:
        self.autostart('sin_server')
        # syncdb:
        print self.command('su %s -c "python %s syncdb --noinput 2>&1"' % (self.user,
                                                                           os.path.join(self.home, 'app/manage.py')))
        print self.command('su %s -c "python %s -i 2>&1"' % (self.user,
                                                             os.path.join(self.home, 'app/sin_server.py')))
        print self.command('%s restart' % sin_server)

      self.autostart('sin_agent')
      print self.command('%s restart' % sin_agent)

    # Cleanup:
    try: os.remove(tmpfile_local)
    except: pass
    try: self.sftp.remove(tmpfile)
    except: pass
    try: self.sftp.remove(tmp_sin_server)
    except: pass
    try: self.sftp.remove(tmp_sin_agent)
    except: pass

    if not self.check_sin():
      raise Exception("sin install failed!")
    print 'sin installed.'

  def deploy(self):
    if not self.base:
      print 'Please call get_deployer() to get your deployer.'
      sys.exit(1)

    self.install_zkpython()
    self.install_setuptools()
    self.install_django()
    self.install_twisted()
    self.install_cronolog()
    self.install_pyparsing()
    self.install_pysensei()
    self.install_sin()

class DeployerRHEL6_X86_64(BaseDeployer):
  def __init__(self, *args, **kwargs):
    super(DeployerRHEL6_X86_64, self).__init__(*args, **kwargs)

  def autostart(self, service, on=True):
    if on:
      print self.command('chkconfig %s on' % service)
    else:
      print self.command('chkconfig %s off' % service)

  def do_install_zkpython(self):
    print 'Installing zkpython...'
    tmpfile = 'zkpython.tar.gz'
    try: self.sftp.remove(tmpfile)
    except: pass
    self.sftp.put(os.path.join(SIN_HOME, 'lib/zk-client/linux-x86_64-2.6/zkpython.tar.gz'), tmpfile)
    self.command('tar -C / -xzf %s' % tmpfile)
    try: self.sftp.remove(tmpfile)
    except: pass
    if not self.check_zkpython():
      raise Exception("zkpython install failed!")
    print 'zkpython installed.'

  def do_install_setuptools(self):
    print 'Installing setuptools...'
    print self.command('yum -y install python-setuptools')
    if not self.check_setuptools():
      raise Exception("setuptools install failed!")
    print 'setuptools installed.'

  def do_install_twisted(self):
    print 'Installing twisted...'
    print self.command('yum -y install python-twisted-web')
    if not self.check_twisted():
      raise Exception("twisted install failed!")
    print 'twisted installed.'

  def do_install_cronolog(self):
    print 'Installing cronolog...'
    tmpfile = 'cronolog-1.6.2-10.el6.x86_64.rpm'
    try: self.sftp.remove(tmpfile)
    except: pass
    self.sftp.put(os.path.join(SIN_HOME, 'lib/cronolog/%s' % tmpfile), tmpfile)
    print self.command('rpm -i --quiet %s' % tmpfile)
    try: self.sftp.remove(tmpfile)
    except: pass
    if not self.check_cronolog():
      raise Exception("cronolog install failed!")
    print 'cronolog installed.'

class DeployerDarwin_I386(BaseDeployer):
  def autostart(self, service, on=True):
    print "Warn: autostart not implemented."

  def __init__(self, *args, **kwargs):
    super(DeployerDarwin_I386, self).__init__(*args, **kwargs)

  def do_install_zkpython(self):
    print 'Installing zkpython...'
    tmpfile = 'zkpython.tar.gz'
    try: self.sftp.remove(tmpfile)
    except: pass
    self.sftp.put(os.path.join(SIN_HOME, 'lib/zk-client/darwin-i386-2.6/zkpython.tar.gz'), tmpfile)
    self.command('tar -C / -xzf %s' % tmpfile)
    try: self.sftp.remove(tmpfile)
    except: pass
    if not self.check_zkpython():
      raise Exception("zkpython install failed!")
    print 'zkpython installed.'

  def do_install_cronolog(self):
    print 'Installing cronolog...'
    tmpfile = 'cronolog.tar.gz'
    try: self.sftp.remove(tmpfile)
    except: pass
    self.sftp.put(os.path.join(SIN_HOME, 'lib/cronolog/cronolog-1.6.2.darwin.i386.tar.gz'), tmpfile)
    self.command('tar -C / -xzf %s' % tmpfile)
    try: self.sftp.remove(tmpfile)
    except: pass
    if not self.check_cronolog():
      raise Exception("cronolog install failed!")
    print 'cronolog installed.'

class DeployerDarwin_X86_64(DeployerDarwin_I386):
  def __init__(self, *args, **kwargs):
    super(DeployerDarwin_X86_64, self).__init__(*args, **kwargs)

  def do_install_zkpython(self):
    print 'Installing zkpython...'
    tmpfile = 'zkpython.tar.gz'
    try: self.sftp.remove(tmpfile)
    except: pass
    self.sftp.put(os.path.join(SIN_HOME, 'lib/zk-client/darwin-x86_64-2.6/zkpython.tar.gz'), tmpfile)
    self.command('tar -C / -xzf %s' % tmpfile)
    try: self.sftp.remove(tmpfile)
    except: pass
    if not self.check_zkpython():
      raise Exception("zkpython install failed!")
    print 'zkpython installed.'

  def do_install_cronolog(self):
    print 'Installing cronolog...'
    tmpfile = 'cronolog.tar.gz'
    try: self.sftp.remove(tmpfile)
    except: pass
    self.sftp.put(os.path.join(SIN_HOME, 'lib/cronolog/cronolog-1.6.2.darwin.x86_64.tar.gz'), tmpfile)
    self.command('tar -C / -xzf %s' % tmpfile)
    try: self.sftp.remove(tmpfile)
    except: pass
    if not self.check_cronolog():
      raise Exception("cronolog install failed!")
    print 'cronolog installed.'

def main(argv):
  usage = "usage: %prog [options] <install dir>"
  parser = OptionParser(usage=usage)
  parser.add_option("-l", "--login", type="string", dest="login", default=None, help="The login user you want to run the deployment script on each node.")
  parser.add_option("-u", "--user", type="string", dest="user", default="root", help="The user sin will running as.")
  parser.add_option("-g", "--upgrade", action="store_true", dest="upgrade", help="Install or upgrade if installed.")
  (options, args) = parser.parse_args()
  if len(args) != 1:
    parser.error("Please give me a install dir (/var/sin for example).")
  home = args[0]

  server = True
  sin_nodes = sorted(list(settings.SIN_NODES.get('nodes', [])), key=lambda node:node['node_id'])
  for node in sin_nodes:
    deployer = BaseDeployer(
                              node['host'],
                              home,
                              node['node_id'],
                              login   = options.login,
                              server  = server,
                              user    = options.user,
                              upgrade = options.upgrade
                           ).get_deployer()
    deployer.deploy()
    server = False

def target(*args):
  return main, None

if __name__ == '__main__':
  main(sys.argv)
