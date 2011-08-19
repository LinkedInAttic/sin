from django.template import loader, TemplateDoesNotExist

try:  # initialize loaders
  loader.get_template('dummy_template.html')
except TemplateDoesNotExist:
  pass

def load_template_source(template_name):
  source = None
  for l in loader.template_source_loaders:
    try:
      source, origin = l.load_template_source(template_name)
    except TemplateDoesNotExist:
      pass

  if source is None:
    raise TemplateDoesNotExist(template_name)
  return source, origin

