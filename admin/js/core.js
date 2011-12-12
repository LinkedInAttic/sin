/*!
 * jQuery blockUI plugin
 * Version 2.39 (23-MAY-2011)
 * @requires jQuery v1.2.3 or later
 *
 * Examples at: http://malsup.com/jquery/block/
 * Copyright (c) 2007-2010 M. Alsup
 * Dual licensed under the MIT and GPL licenses:
 * http://www.opensource.org/licenses/mit-license.php
 * http://www.gnu.org/licenses/gpl.html
 *
 * Thanks to Amir-Hossein Sobhi for some excellent contributions!
 */

;(function($) {

if (/1\.(0|1|2)\.(0|1|2)/.test($.fn.jquery) || /^1.1/.test($.fn.jquery)) {
  alert('blockUI requires jQuery v1.2.3 or later!  You are using v' + $.fn.jquery);
  return;
}

$.fn._fadeIn = $.fn.fadeIn;

var noOp = function() {};

// this bit is to ensure we don't call setExpression when we shouldn't (with extra muscle to handle
// retarded userAgent strings on Vista)
var mode = document.documentMode || 0;
var setExpr = $.browser.msie && (($.browser.version < 8 && !mode) || mode < 8);
var ie6 = $.browser.msie && /MSIE 6.0/.test(navigator.userAgent) && !mode;

// global $ methods for blocking/unblocking the entire page
$.blockUI   = function(opts) { install(window, opts); };
$.unblockUI = function(opts) { remove(window, opts); };

// convenience method for quick growl-like notifications  (http://www.google.com/search?q=growl)
$.growlUI = function(title, message, timeout, onClose) {
  var $m = $('<div class="growlUI"></div>');
  if (title) $m.append('<h1>'+title+'</h1>');
  if (message) $m.append('<h2>'+message+'</h2>');
  if (timeout == undefined) timeout = 3000;
  $.blockUI({
    message: $m, fadeIn: 700, fadeOut: 1000, centerY: false,
    timeout: timeout, showOverlay: false,
    onUnblock: onClose, 
    css: $.blockUI.defaults.growlCSS
  });
};

// plugin method for blocking element content
$.fn.block = function(opts) {
  return this.unblock({ fadeOut: 0 }).each(function() {
    if ($.css(this,'position') == 'static')
      this.style.position = 'relative';
    if ($.browser.msie)
      this.style.zoom = 1; // force 'hasLayout'
    install(this, opts);
  });
};

// plugin method for unblocking element content
$.fn.unblock = function(opts) {
  return this.each(function() {
    remove(this, opts);
  });
};

$.blockUI.version = 2.39; // 2nd generation blocking at no extra cost!

// override these in your code to change the default behavior and style
$.blockUI.defaults = {
  // message displayed when blocking (use null for no message)
  message:  '<h1>Please wait...</h1>',

  title: null,    // title string; only used when theme == true
  draggable: true,  // only used when theme == true (requires jquery-ui.js to be loaded)
  
  theme: false, // set to true to use with jQuery UI themes
  
  // styles for the message when blocking; if you wish to disable
  // these and use an external stylesheet then do this in your code:
  // $.blockUI.defaults.css = {};
  css: {
    padding:  0,
    margin:   0,
    width:    '30%',
    top:    '40%',
    left:   '35%',
    textAlign:  'center',
    color:    '#000',
    border:   '3px solid #aaa',
    backgroundColor:'#fff',
    cursor:   'wait'
  },
  
  // minimal style set used when themes are used
  themedCSS: {
    width:  '30%',
    top:  '40%',
    left: '35%'
  },

  // styles for the overlay
  overlayCSS:  {
    backgroundColor: '#000',
    opacity:       0.6,
    cursor:        'wait'
  },

  // styles applied when using $.growlUI
  growlCSS: {
    width:    '350px',
    top:    '10px',
    left:     '',
    right:    '10px',
    border:   'none',
    padding:  '5px',
    opacity:  0.6,
    cursor:   'default',
    color:    '#fff',
    backgroundColor: '#000',
    '-webkit-border-radius': '10px',
    '-moz-border-radius':  '10px',
    'border-radius':     '10px'
  },
  
  // IE issues: 'about:blank' fails on HTTPS and javascript:false is s-l-o-w
  // (hat tip to Jorge H. N. de Vasconcelos)
  iframeSrc: /^https/i.test(window.location.href || '') ? 'javascript:false' : 'about:blank',

  // force usage of iframe in non-IE browsers (handy for blocking applets)
  forceIframe: false,

  // z-index for the blocking overlay
  baseZ: 1000,

  // set these to true to have the message automatically centered
  centerX: true, // <-- only effects element blocking (page block controlled via css above)
  centerY: true,

  // allow body element to be stetched in ie6; this makes blocking look better
  // on "short" pages.  disable if you wish to prevent changes to the body height
  allowBodyStretch: true,

  // enable if you want key and mouse events to be disabled for content that is blocked
  bindEvents: true,

  // be default blockUI will supress tab navigation from leaving blocking content
  // (if bindEvents is true)
  constrainTabKey: true,

  // fadeIn time in millis; set to 0 to disable fadeIn on block
  fadeIn:  200,

  // fadeOut time in millis; set to 0 to disable fadeOut on unblock
  fadeOut:  400,

  // time in millis to wait before auto-unblocking; set to 0 to disable auto-unblock
  timeout: 0,

  // disable if you don't want to show the overlay
  showOverlay: true,

  // if true, focus will be placed in the first available input field when
  // page blocking
  focusInput: true,

  // suppresses the use of overlay styles on FF/Linux (due to performance issues with opacity)
  applyPlatformOpacityRules: true,
  
  // callback method invoked when fadeIn has completed and blocking message is visible
  onBlock: null,

  // callback method invoked when unblocking has completed; the callback is
  // passed the element that has been unblocked (which is the window object for page
  // blocks) and the options that were passed to the unblock call:
  //   onUnblock(element, options)
  onUnblock: null,

  // don't ask; if you really must know: http://groups.google.com/group/jquery-en/browse_thread/thread/36640a8730503595/2f6a79a77a78e493#2f6a79a77a78e493
  quirksmodeOffsetHack: 4,

  // class name of the message block
  blockMsgClass: 'blockMsg'
};

// private data and functions follow...

var pageBlock = null;
var pageBlockEls = [];

function install(el, opts) {
  var full = (el == window);
  var msg = opts && opts.message !== undefined ? opts.message : undefined;
  opts = $.extend({}, $.blockUI.defaults, opts || {});
  opts.overlayCSS = $.extend({}, $.blockUI.defaults.overlayCSS, opts.overlayCSS || {});
  var css = $.extend({}, $.blockUI.defaults.css, opts.css || {});
  var themedCSS = $.extend({}, $.blockUI.defaults.themedCSS, opts.themedCSS || {});
  msg = msg === undefined ? opts.message : msg;

  // remove the current block (if there is one)
  if (full && pageBlock)
    remove(window, {fadeOut:0});

  // if an existing element is being used as the blocking content then we capture
  // its current place in the DOM (and current display style) so we can restore
  // it when we unblock
  if (msg && typeof msg != 'string' && (msg.parentNode || msg.jquery)) {
    var node = msg.jquery ? msg[0] : msg;
    var data = {};
    $(el).data('blockUI.history', data);
    data.el = node;
    data.parent = node.parentNode;
    data.display = node.style.display;
    data.position = node.style.position;
    if (data.parent)
      data.parent.removeChild(node);
  }

  $(el).data('blockUI.onUnblock', opts.onUnblock);
  var z = opts.baseZ;

  // blockUI uses 3 layers for blocking, for simplicity they are all used on every platform;
  // layer1 is the iframe layer which is used to supress bleed through of underlying content
  // layer2 is the overlay layer which has opacity and a wait cursor (by default)
  // layer3 is the message content that is displayed while blocking

  var lyr1 = ($.browser.msie || opts.forceIframe) 
    ? $('<iframe class="blockUI" style="z-index:'+ (z++) +';display:none;border:none;margin:0;padding:0;position:absolute;width:100%;height:100%;top:0;left:0" src="'+opts.iframeSrc+'"></iframe>')
    : $('<div class="blockUI" style="display:none"></div>');
  
  var lyr2 = opts.theme 
    ? $('<div class="blockUI blockOverlay ui-widget-overlay" style="z-index:'+ (z++) +';display:none"></div>')
    : $('<div class="blockUI blockOverlay" style="z-index:'+ (z++) +';display:none;border:none;margin:0;padding:0;width:100%;height:100%;top:0;left:0"></div>');

  var lyr3, s;
  if (opts.theme && full) {
    s = '<div class="blockUI ' + opts.blockMsgClass + ' blockPage ui-dialog ui-widget ui-corner-all" style="z-index:'+(z+10)+';display:none;position:fixed">' +
        '<div class="ui-widget-header ui-dialog-titlebar ui-corner-all blockTitle">'+(opts.title || '&nbsp;')+'</div>' +
        '<div class="ui-widget-content ui-dialog-content"></div>' +
      '</div>';
  }
  else if (opts.theme) {
    s = '<div class="blockUI ' + opts.blockMsgClass + ' blockElement ui-dialog ui-widget ui-corner-all" style="z-index:'+(z+10)+';display:none;position:absolute">' +
        '<div class="ui-widget-header ui-dialog-titlebar ui-corner-all blockTitle">'+(opts.title || '&nbsp;')+'</div>' +
        '<div class="ui-widget-content ui-dialog-content"></div>' +
      '</div>';
  }
  else if (full) {
    s = '<div class="blockUI ' + opts.blockMsgClass + ' blockPage" style="z-index:'+(z+10)+';display:none;position:fixed"></div>';
  }      
  else {
    s = '<div class="blockUI ' + opts.blockMsgClass + ' blockElement" style="z-index:'+(z+10)+';display:none;position:absolute"></div>';
  }
  lyr3 = $(s);

  // if we have a message, style it
  if (msg) {
    if (opts.theme) {
      lyr3.css(themedCSS);
      lyr3.addClass('ui-widget-content');
    }
    else 
      lyr3.css(css);
  }

  // style the overlay
  if (!opts.theme && (!opts.applyPlatformOpacityRules || !($.browser.mozilla && /Linux/.test(navigator.platform))))
    lyr2.css(opts.overlayCSS);
  lyr2.css('position', full ? 'fixed' : 'absolute');

  // make iframe layer transparent in IE
  if ($.browser.msie || opts.forceIframe)
    lyr1.css('opacity',0.0);

  //$([lyr1[0],lyr2[0],lyr3[0]]).appendTo(full ? 'body' : el);
  var layers = [lyr1,lyr2,lyr3], $par = full ? $('body') : $(el);
  $.each(layers, function() {
    this.appendTo($par);
  });
  
  if (opts.theme && opts.draggable && $.fn.draggable) {
    lyr3.draggable({
      handle: '.ui-dialog-titlebar',
      cancel: 'li'
    });
  }

  // ie7 must use absolute positioning in quirks mode and to account for activex issues (when scrolling)
  var expr = setExpr && (!$.boxModel || $('object,embed', full ? null : el).length > 0);
  if (ie6 || expr) {
    // give body 100% height
    if (full && opts.allowBodyStretch && $.boxModel)
      $('html,body').css('height','100%');

    // fix ie6 issue when blocked element has a border width
    if ((ie6 || !$.boxModel) && !full) {
      var t = sz(el,'borderTopWidth'), l = sz(el,'borderLeftWidth');
      var fixT = t ? '(0 - '+t+')' : 0;
      var fixL = l ? '(0 - '+l+')' : 0;
    }

    // simulate fixed position
    $.each([lyr1,lyr2,lyr3], function(i,o) {
      var s = o[0].style;
      s.position = 'absolute';
      if (i < 2) {
        full ? s.setExpression('height','Math.max(document.body.scrollHeight, document.body.offsetHeight) - (jQuery.boxModel?0:'+opts.quirksmodeOffsetHack+') + "px"')
           : s.setExpression('height','this.parentNode.offsetHeight + "px"');
        full ? s.setExpression('width','jQuery.boxModel && document.documentElement.clientWidth || document.body.clientWidth + "px"')
           : s.setExpression('width','this.parentNode.offsetWidth + "px"');
        if (fixL) s.setExpression('left', fixL);
        if (fixT) s.setExpression('top', fixT);
      }
      else if (opts.centerY) {
        if (full) s.setExpression('top','(document.documentElement.clientHeight || document.body.clientHeight) / 2 - (this.offsetHeight / 2) + (blah = document.documentElement.scrollTop ? document.documentElement.scrollTop : document.body.scrollTop) + "px"');
        s.marginTop = 0;
      }
      else if (!opts.centerY && full) {
        var top = (opts.css && opts.css.top) ? parseInt(opts.css.top) : 0;
        var expression = '((document.documentElement.scrollTop ? document.documentElement.scrollTop : document.body.scrollTop) + '+top+') + "px"';
        s.setExpression('top',expression);
      }
    });
  }

  // show the message
  if (msg) {
    if (opts.theme)
      lyr3.find('.ui-widget-content').append(msg);
    else
      lyr3.append(msg);
    if (msg.jquery || msg.nodeType)
      $(msg).show();
  }

  if (($.browser.msie || opts.forceIframe) && opts.showOverlay)
    lyr1.show(); // opacity is zero
  if (opts.fadeIn) {
    var cb = opts.onBlock ? opts.onBlock : noOp;
    var cb1 = (opts.showOverlay && !msg) ? cb : noOp;
    var cb2 = msg ? cb : noOp;
    if (opts.showOverlay)
      lyr2._fadeIn(opts.fadeIn, cb1);
    if (msg)
      lyr3._fadeIn(opts.fadeIn, cb2);
  }
  else {
    if (opts.showOverlay)
      lyr2.show();
    if (msg)
      lyr3.show();
    if (opts.onBlock)
      opts.onBlock();
  }

  // bind key and mouse events
  bind(1, el, opts);

  if (full) {
    pageBlock = lyr3[0];
    pageBlockEls = $(':input:enabled:visible',pageBlock);
    if (opts.focusInput)
      setTimeout(focus, 20);
  }
  else
    center(lyr3[0], opts.centerX, opts.centerY);

  if (opts.timeout) {
    // auto-unblock
    var to = setTimeout(function() {
      full ? $.unblockUI(opts) : $(el).unblock(opts);
    }, opts.timeout);
    $(el).data('blockUI.timeout', to);
  }
};

// remove the block
function remove(el, opts) {
  var full = (el == window);
  var $el = $(el);
  var data = $el.data('blockUI.history');
  var to = $el.data('blockUI.timeout');
  if (to) {
    clearTimeout(to);
    $el.removeData('blockUI.timeout');
  }
  opts = $.extend({}, $.blockUI.defaults, opts || {});
  bind(0, el, opts); // unbind events

  if (opts.onUnblock === null) {
    opts.onUnblock = $el.data('blockUI.onUnblock');
    $el.removeData('blockUI.onUnblock');
  }

  var els;
  if (full) // crazy selector to handle odd field errors in ie6/7
    els = $('body').children().filter('.blockUI').add('body > .blockUI');
  else
    els = $('.blockUI', el);

  if (full)
    pageBlock = pageBlockEls = null;

  if (opts.fadeOut) {
    els.fadeOut(opts.fadeOut);
    setTimeout(function() { reset(els,data,opts,el); }, opts.fadeOut);
  }
  else
    reset(els, data, opts, el);
};

// move blocking element back into the DOM where it started
function reset(els,data,opts,el) {
  els.each(function(i,o) {
    // remove via DOM calls so we don't lose event handlers
    if (this.parentNode)
      this.parentNode.removeChild(this);
  });

  if (data && data.el) {
    data.el.style.display = data.display;
    data.el.style.position = data.position;
    if (data.parent)
      data.parent.appendChild(data.el);
    $(el).removeData('blockUI.history');
  }

  if (typeof opts.onUnblock == 'function')
    opts.onUnblock(el,opts);
};

// bind/unbind the handler
function bind(b, el, opts) {
  var full = el == window, $el = $(el);

  // don't bother unbinding if there is nothing to unbind
  if (!b && (full && !pageBlock || !full && !$el.data('blockUI.isBlocked')))
    return;
  if (!full)
    $el.data('blockUI.isBlocked', b);

  // don't bind events when overlay is not in use or if bindEvents is false
  if (!opts.bindEvents || (b && !opts.showOverlay)) 
    return;

  // bind anchors and inputs for mouse and key events
  var events = 'mousedown mouseup keydown keypress';
  b ? $(document).bind(events, opts, handler) : $(document).unbind(events, handler);

// former impl...
//     var $e = $('a,:input');
//     b ? $e.bind(events, opts, handler) : $e.unbind(events, handler);
};

// event handler to suppress keyboard/mouse events when blocking
function handler(e) {
  // allow tab navigation (conditionally)
  if (e.keyCode && e.keyCode == 9) {
    if (pageBlock && e.data.constrainTabKey) {
      var els = pageBlockEls;
      var fwd = !e.shiftKey && e.target === els[els.length-1];
      var back = e.shiftKey && e.target === els[0];
      if (fwd || back) {
        setTimeout(function(){focus(back)},10);
        return false;
      }
    }
  }
  var opts = e.data;
  // allow events within the message content
  if ($(e.target).parents('div.' + opts.blockMsgClass).length > 0)
    return true;

  // allow events for content that is not being blocked
  return $(e.target).parents().children().filter('div.blockUI').length == 0;
};

function focus(back) {
  if (!pageBlockEls)
    return;
  var e = pageBlockEls[back===true ? pageBlockEls.length-1 : 0];
  if (e)
    e.focus();
};

function center(el, x, y) {
  var p = el.parentNode, s = el.style;
  var l = ((p.offsetWidth - el.offsetWidth)/2) - sz(p,'borderLeftWidth');
  var t = ((p.offsetHeight - el.offsetHeight)/2) - sz(p,'borderTopWidth');
  if (x) s.left = l > 0 ? (l+'px') : '0';
  if (y) s.top  = t > 0 ? (t+'px') : '0';
};

function sz(el, p) {
  return parseInt($.css(el,p))||0;
};

})(jQuery);

/*
Shameless port of a shameless port
@defunkt => @janl => @aq
 
See http://github.com/defunkt/mustache for more info.
*/
 
;(function($) {

/*
  mustache.js - Logic-less templates in JavaScript

  See http://mustache.github.com/ for more info.
*/

var Mustache = function() {
  var Renderer = function() {};

  Renderer.prototype = {
    otag: "{{",
    ctag: "}}",
    pragmas: {},
    buffer: [],
    pragmas_implemented: {
      "IMPLICIT-ITERATOR": true
    },
    context: {},

    render: function(template, context, partials, in_recursion) {
      // reset buffer & set context
      if(!in_recursion) {
        this.context = context;
        this.buffer = []; // TODO: make this non-lazy
      }

      // fail fast
      if(!this.includes("", template)) {
        if(in_recursion) {
          return template;
        } else {
          this.send(template);
          return;
        }
      }

      template = this.render_pragmas(template);
      var html = this.render_section(template, context, partials);
      if(in_recursion) {
        return this.render_tags(html, context, partials, in_recursion);
      }

      this.render_tags(html, context, partials, in_recursion);
    },

    /*
      Sends parsed lines
    */
    send: function(line) {
      if(line != "") {
        this.buffer.push(line);
      }
    },

    /*
      Looks for %PRAGMAS
    */
    render_pragmas: function(template) {
      // no pragmas
      if(!this.includes("%", template)) {
        return template;
      }

      var that = this;
      var regex = new RegExp(this.otag + "%([\\w-]+) ?([\\w]+=[\\w]+)?" +
            this.ctag);
      return template.replace(regex, function(match, pragma, options) {
        if(!that.pragmas_implemented[pragma]) {
          throw({message: 
            "This implementation of mustache doesn't understand the '" +
            pragma + "' pragma"});
        }
        that.pragmas[pragma] = {};
        if(options) {
          var opts = options.split("=");
          that.pragmas[pragma][opts[0]] = opts[1];
        }
        return "";
        // ignore unknown pragmas silently
      });
    },

    /*
      Tries to find a partial in the curent scope and render it
    */
    render_partial: function(name, context, partials) {
      name = this.trim(name);
      if(!partials || partials[name] === undefined) {
        throw({message: "unknown_partial '" + name + "'"});
      }
      if(typeof(context[name]) != "object") {
        return this.render(partials[name], context, partials, true);
      }
      return this.render(partials[name], context[name], partials, true);
    },

    /*
      Renders inverted (^) and normal (#) sections
    */
    render_section: function(template, context, partials) {
      if(!this.includes("#", template) && !this.includes("^", template)) {
        return template;
      }

      var that = this;
      // CSW - Added "+?" so it finds the tighest bound, not the widest
      var regex = new RegExp(this.otag + "(\\^|\\#)\\s*(.+)\\s*" + this.ctag +
              "\n*([\\s\\S]+?)" + this.otag + "\\/\\s*\\2\\s*" + this.ctag +
              "\\s*", "mg");

      // for each {{#foo}}{{/foo}} section do...
      return template.replace(regex, function(match, type, name, content) {
        var value = that.find(name, context);
        if(type == "^") { // inverted section
          if(!value || that.is_array(value) && value.length === 0) {
            // false or empty list, render it
            return that.render(content, context, partials, true);
          } else {
            return "";
          }
        } else if(type == "#") { // normal section
          if(that.is_array(value)) { // Enumerable, Let's loop!
            return that.map(value, function(row) {
              return that.render(content, that.create_context(row),
                partials, true);
            }).join("");
          } else if(that.is_object(value)) { // Object, Use it as subcontext!
            return that.render(content, that.create_context(value),
              partials, true);
          } else if(typeof value === "function") {
            // higher order section
            return value.call(context, content, function(text) {
              return that.render(text, context, partials, true);
            });
          } else if(value) { // boolean section
            return that.render(content, context, partials, true);
          } else {
            return "";
          }
        }
      });
    },

    /*
      Replace {{foo}} and friends with values from our view
    */
    render_tags: function(template, context, partials, in_recursion) {
      // tit for tat
      var that = this;

      var new_regex = function() {
        return new RegExp(that.otag + "(=|!|>|\\{|%)?([^\\/#\\^]+?)\\1?" +
          that.ctag + "+", "g");
      };

      var regex = new_regex();
      var tag_replace_callback = function(match, operator, name) {
        switch(operator) {
        case "!": // ignore comments
          return "";
        case "=": // set new delimiters, rebuild the replace regexp
          that.set_delimiters(name);
          regex = new_regex();
          return "";
        case ">": // render partial
          return that.render_partial(name, context, partials);
        case "{": // the triple mustache is unescaped
          return that.find(name, context);
        default: // escape the value
          return that.escape(that.find(name, context));
        }
      };
      var lines = template.split("\n");
      for(var i = 0; i < lines.length; i++) {
        lines[i] = lines[i].replace(regex, tag_replace_callback, this);
        if(!in_recursion) {
          this.send(lines[i]);
        }
      }

      if(in_recursion) {
        return lines.join("\n");
      }
    },

    set_delimiters: function(delimiters) {
      var dels = delimiters.split(" ");
      this.otag = this.escape_regex(dels[0]);
      this.ctag = this.escape_regex(dels[1]);
    },

    escape_regex: function(text) {
      // thank you Simon Willison
      if(!arguments.callee.sRE) {
        var specials = [
          '/', '.', '*', '+', '?', '|',
          '(', ')', '[', ']', '{', '}', '\\'
        ];
        arguments.callee.sRE = new RegExp(
          '(\\' + specials.join('|\\') + ')', 'g'
        );
      }
      return text.replace(arguments.callee.sRE, '\\$1');
    },

    /*
      find `name` in current `context`. That is find me a value
      from the view object
    */
    find: function(name, context) {
      name = this.trim(name);
      var path = name.split('.');

      function get_value(obj, path) {
        var val = obj;
        if (!path || path.length <= 0)
          return undefined;

        try {
          for (var i=0; i<path.length; ++i) {
            if (!val)
              return undefined;
            val= val[path[i]];
          }
        }
        catch(e) {
          console.log(e);
          return undefined;
        }
        return val;
      }

      // Checks whether a value is thruthy or false or 0
      function is_kinda_truthy(bool) {
        return bool === false || bool === 0 || bool;
      }

      var value;
      if(is_kinda_truthy(get_value(context, path))) {
        value = get_value(context, path);
      } else if(is_kinda_truthy(get_value(this.context, path))) {
        value = get_value(this.context, path);
      }

      if(typeof value === "function") {
        value = value.apply(context);
      }
      if(value !== undefined) {
        if (/(object|array)/i.test(jQuery.type(value))) {
          var json = js_beautify(jQuery.toJSON(value));
          value.toString = function() {
            return json;
          };
          return value;
        }
        return value;
      }
      // silently ignore unkown variables
      return "";
    },

    // Utility methods

    /* includes tag */
    includes: function(needle, haystack) {
      return haystack.indexOf(this.otag + needle) != -1;
    },

    /*
      Does away with nasty characters
    */
    escape: function(s) {
      s = String(s === null ? "" : s);
      return s.replace(/&(?!\w+;)|["'<>\\]/g, function(s) {
        switch(s) {
        case "&": return "&amp;";
        case "\\": return "\\\\";
        case '"': return '&quot;';
        case "'": return '&#39;';
        case "<": return "&lt;";
        case ">": return "&gt;";
        default: return s;
        }
      });
    },

    // by @langalex, support for arrays of strings
    create_context: function(_context) {
      if(this.is_object(_context)) {
        return _context;
      } else {
        var iterator = ".";
        if(this.pragmas["IMPLICIT-ITERATOR"]) {
          iterator = this.pragmas["IMPLICIT-ITERATOR"].iterator;
        }
        var ctx = {};
        ctx[iterator] = _context;
        return ctx;
      }
    },

    is_object: function(a) {
      return a && typeof a == "object";
    },

    is_array: function(a) {
      return Object.prototype.toString.call(a) === '[object Array]';
    },

    /*
      Gets rid of leading and trailing whitespace
    */
    trim: function(s) {
      return s.replace(/^\s*|\s*$/g, "");
    },

    /*
      Why, why, why? Because IE. Cry, cry cry.
    */
    map: function(array, fn) {
      if (typeof array.map == "function") {
        return array.map(fn);
      } else {
        var r = [];
        var l = array.length;
        for(var i = 0; i < l; i++) {
          r.push(fn(array[i]));
        }
        return r;
      }
    }
  };

  return({
    name: "mustache.js",
    version: "0.3.1-dev",

    /*
      Turns a template and view into HTML
    */
    to_html: function(template, view, partials, send_fun) {
      var renderer = new Renderer();
      if(send_fun) {
        renderer.send = send_fun;
      }
      renderer.render(template, view, partials);
      if(!send_fun) {
        return renderer.buffer.join("\n");
      }
    }
  });
}();

  $.mustache = function(template, view, partials) {
    return Mustache.to_html(template, view, partials);
  };

})(jQuery);
//     Underscore.js 1.1.7
//     (c) 2011 Jeremy Ashkenas, DocumentCloud Inc.
//     Underscore is freely distributable under the MIT license.
//     Portions of Underscore are inspired or borrowed from Prototype,
//     Oliver Steele's Functional, and John Resig's Micro-Templating.
//     For all details and documentation:
//     http://documentcloud.github.com/underscore

(function() {

  // Baseline setup
  // --------------

  // Establish the root object, `window` in the browser, or `global` on the server.
  var root = this;

  // Save the previous value of the `_` variable.
  var previousUnderscore = root._;

  // Establish the object that gets returned to break out of a loop iteration.
  var breaker = {};

  // Save bytes in the minified (but not gzipped) version:
  var ArrayProto = Array.prototype, ObjProto = Object.prototype, FuncProto = Function.prototype;

  // Create quick reference variables for speed access to core prototypes.
  var slice            = ArrayProto.slice,
      unshift          = ArrayProto.unshift,
      toString         = ObjProto.toString,
      hasOwnProperty   = ObjProto.hasOwnProperty;

  // All **ECMAScript 5** native function implementations that we hope to use
  // are declared here.
  var
    nativeForEach      = ArrayProto.forEach,
    nativeMap          = ArrayProto.map,
    nativeReduce       = ArrayProto.reduce,
    nativeReduceRight  = ArrayProto.reduceRight,
    nativeFilter       = ArrayProto.filter,
    nativeEvery        = ArrayProto.every,
    nativeSome         = ArrayProto.some,
    nativeIndexOf      = ArrayProto.indexOf,
    nativeLastIndexOf  = ArrayProto.lastIndexOf,
    nativeIsArray      = Array.isArray,
    nativeKeys         = Object.keys,
    nativeBind         = FuncProto.bind;

  // Create a safe reference to the Underscore object for use below.
  var _ = function(obj) { return new wrapper(obj); };

  // Export the Underscore object for **CommonJS**, with backwards-compatibility
  // for the old `require()` API. If we're not in CommonJS, add `_` to the
  // global object.
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = _;
    _._ = _;
  } else {
    // Exported as a string, for Closure Compiler "advanced" mode.
    root['_'] = _;
  }

  // Current version.
  _.VERSION = '1.1.7';

  // Collection Functions
  // --------------------

  // The cornerstone, an `each` implementation, aka `forEach`.
  // Handles objects with the built-in `forEach`, arrays, and raw objects.
  // Delegates to **ECMAScript 5**'s native `forEach` if available.
  var each = _.each = _.forEach = function(obj, iterator, context) {
    if (obj == null) return;
    if (nativeForEach && obj.forEach === nativeForEach) {
      obj.forEach(iterator, context);
    } else if (obj.length === +obj.length) {
      for (var i = 0, l = obj.length; i < l; i++) {
        if (i in obj && iterator.call(context, obj[i], i, obj) === breaker) return;
      }
    } else {
      for (var key in obj) {
        if (hasOwnProperty.call(obj, key)) {
          if (iterator.call(context, obj[key], key, obj) === breaker) return;
        }
      }
    }
  };

  // Return the results of applying the iterator to each element.
  // Delegates to **ECMAScript 5**'s native `map` if available.
  _.map = function(obj, iterator, context) {
    var results = [];
    if (obj == null) return results;
    if (nativeMap && obj.map === nativeMap) return obj.map(iterator, context);
    each(obj, function(value, index, list) {
      results[results.length] = iterator.call(context, value, index, list);
    });
    return results;
  };

  // **Reduce** builds up a single result from a list of values, aka `inject`,
  // or `foldl`. Delegates to **ECMAScript 5**'s native `reduce` if available.
  _.reduce = _.foldl = _.inject = function(obj, iterator, memo, context) {
    var initial = memo !== void 0;
    if (obj == null) obj = [];
    if (nativeReduce && obj.reduce === nativeReduce) {
      if (context) iterator = _.bind(iterator, context);
      return initial ? obj.reduce(iterator, memo) : obj.reduce(iterator);
    }
    each(obj, function(value, index, list) {
      if (!initial) {
        memo = value;
        initial = true;
      } else {
        memo = iterator.call(context, memo, value, index, list);
      }
    });
    if (!initial) throw new TypeError("Reduce of empty array with no initial value");
    return memo;
  };

  // The right-associative version of reduce, also known as `foldr`.
  // Delegates to **ECMAScript 5**'s native `reduceRight` if available.
  _.reduceRight = _.foldr = function(obj, iterator, memo, context) {
    if (obj == null) obj = [];
    if (nativeReduceRight && obj.reduceRight === nativeReduceRight) {
      if (context) iterator = _.bind(iterator, context);
      return memo !== void 0 ? obj.reduceRight(iterator, memo) : obj.reduceRight(iterator);
    }
    var reversed = (_.isArray(obj) ? obj.slice() : _.toArray(obj)).reverse();
    return _.reduce(reversed, iterator, memo, context);
  };

  // Return the first value which passes a truth test. Aliased as `detect`.
  _.find = _.detect = function(obj, iterator, context) {
    var result;
    any(obj, function(value, index, list) {
      if (iterator.call(context, value, index, list)) {
        result = value;
        return true;
      }
    });
    return result;
  };

  // Return all the elements that pass a truth test.
  // Delegates to **ECMAScript 5**'s native `filter` if available.
  // Aliased as `select`.
  _.filter = _.select = function(obj, iterator, context) {
    var results = [];
    if (obj == null) return results;
    if (nativeFilter && obj.filter === nativeFilter) return obj.filter(iterator, context);
    each(obj, function(value, index, list) {
      if (iterator.call(context, value, index, list)) results[results.length] = value;
    });
    return results;
  };

  // Return all the elements for which a truth test fails.
  _.reject = function(obj, iterator, context) {
    var results = [];
    if (obj == null) return results;
    each(obj, function(value, index, list) {
      if (!iterator.call(context, value, index, list)) results[results.length] = value;
    });
    return results;
  };

  // Determine whether all of the elements match a truth test.
  // Delegates to **ECMAScript 5**'s native `every` if available.
  // Aliased as `all`.
  _.every = _.all = function(obj, iterator, context) {
    var result = true;
    if (obj == null) return result;
    if (nativeEvery && obj.every === nativeEvery) return obj.every(iterator, context);
    each(obj, function(value, index, list) {
      if (!(result = result && iterator.call(context, value, index, list))) return breaker;
    });
    return result;
  };

  // Determine if at least one element in the object matches a truth test.
  // Delegates to **ECMAScript 5**'s native `some` if available.
  // Aliased as `any`.
  var any = _.some = _.any = function(obj, iterator, context) {
    iterator = iterator || _.identity;
    var result = false;
    if (obj == null) return result;
    if (nativeSome && obj.some === nativeSome) return obj.some(iterator, context);
    each(obj, function(value, index, list) {
      if (result |= iterator.call(context, value, index, list)) return breaker;
    });
    return !!result;
  };

  // Determine if a given value is included in the array or object using `===`.
  // Aliased as `contains`.
  _.include = _.contains = function(obj, target) {
    var found = false;
    if (obj == null) return found;
    if (nativeIndexOf && obj.indexOf === nativeIndexOf) return obj.indexOf(target) != -1;
    any(obj, function(value) {
      if (found = value === target) return true;
    });
    return found;
  };

  // Invoke a method (with arguments) on every item in a collection.
  _.invoke = function(obj, method) {
    var args = slice.call(arguments, 2);
    return _.map(obj, function(value) {
      return (method.call ? method || value : value[method]).apply(value, args);
    });
  };

  // Convenience version of a common use case of `map`: fetching a property.
  _.pluck = function(obj, key) {
    return _.map(obj, function(value){ return value[key]; });
  };

  // Return the maximum element or (element-based computation).
  _.max = function(obj, iterator, context) {
    if (!iterator && _.isArray(obj)) return Math.max.apply(Math, obj);
    var result = {computed : -Infinity};
    each(obj, function(value, index, list) {
      var computed = iterator ? iterator.call(context, value, index, list) : value;
      computed >= result.computed && (result = {value : value, computed : computed});
    });
    return result.value;
  };

  // Return the minimum element (or element-based computation).
  _.min = function(obj, iterator, context) {
    if (!iterator && _.isArray(obj)) return Math.min.apply(Math, obj);
    var result = {computed : Infinity};
    each(obj, function(value, index, list) {
      var computed = iterator ? iterator.call(context, value, index, list) : value;
      computed < result.computed && (result = {value : value, computed : computed});
    });
    return result.value;
  };

  // Sort the object's values by a criterion produced by an iterator.
  _.sortBy = function(obj, iterator, context) {
    return _.pluck(_.map(obj, function(value, index, list) {
      return {
        value : value,
        criteria : iterator.call(context, value, index, list)
      };
    }).sort(function(left, right) {
      var a = left.criteria, b = right.criteria;
      return a < b ? -1 : a > b ? 1 : 0;
    }), 'value');
  };

  // Groups the object's values by a criterion produced by an iterator
  _.groupBy = function(obj, iterator) {
    var result = {};
    each(obj, function(value, index) {
      var key = iterator(value, index);
      (result[key] || (result[key] = [])).push(value);
    });
    return result;
  };

  // Use a comparator function to figure out at what index an object should
  // be inserted so as to maintain order. Uses binary search.
  _.sortedIndex = function(array, obj, iterator) {
    iterator || (iterator = _.identity);
    var low = 0, high = array.length;
    while (low < high) {
      var mid = (low + high) >> 1;
      iterator(array[mid]) < iterator(obj) ? low = mid + 1 : high = mid;
    }
    return low;
  };

  // Safely convert anything iterable into a real, live array.
  _.toArray = function(iterable) {
    if (!iterable)                return [];
    if (iterable.toArray)         return iterable.toArray();
    if (_.isArray(iterable))      return slice.call(iterable);
    if (_.isArguments(iterable))  return slice.call(iterable);
    return _.values(iterable);
  };

  // Return the number of elements in an object.
  _.size = function(obj) {
    return _.toArray(obj).length;
  };

  // Array Functions
  // ---------------

  // Get the first element of an array. Passing **n** will return the first N
  // values in the array. Aliased as `head`. The **guard** check allows it to work
  // with `_.map`.
  _.first = _.head = function(array, n, guard) {
    return (n != null) && !guard ? slice.call(array, 0, n) : array[0];
  };

  // Returns everything but the first entry of the array. Aliased as `tail`.
  // Especially useful on the arguments object. Passing an **index** will return
  // the rest of the values in the array from that index onward. The **guard**
  // check allows it to work with `_.map`.
  _.rest = _.tail = function(array, index, guard) {
    return slice.call(array, (index == null) || guard ? 1 : index);
  };

  // Get the last element of an array.
  _.last = function(array) {
    return array[array.length - 1];
  };

  // Trim out all falsy values from an array.
  _.compact = function(array) {
    return _.filter(array, function(value){ return !!value; });
  };

  // Return a completely flattened version of an array.
  _.flatten = function(array) {
    return _.reduce(array, function(memo, value) {
      if (_.isArray(value)) return memo.concat(_.flatten(value));
      memo[memo.length] = value;
      return memo;
    }, []);
  };

  // Return a version of the array that does not contain the specified value(s).
  _.without = function(array) {
    return _.difference(array, slice.call(arguments, 1));
  };

  // Produce a duplicate-free version of the array. If the array has already
  // been sorted, you have the option of using a faster algorithm.
  // Aliased as `unique`.
  _.uniq = _.unique = function(array, isSorted) {
    return _.reduce(array, function(memo, el, i) {
      if (0 == i || (isSorted === true ? _.last(memo) != el : !_.include(memo, el))) memo[memo.length] = el;
      return memo;
    }, []);
  };

  // Produce an array that contains the union: each distinct element from all of
  // the passed-in arrays.
  _.union = function() {
    return _.uniq(_.flatten(arguments));
  };

  // Produce an array that contains every item shared between all the
  // passed-in arrays. (Aliased as "intersect" for back-compat.)
  _.intersection = _.intersect = function(array) {
    var rest = slice.call(arguments, 1);
    return _.filter(_.uniq(array), function(item) {
      return _.every(rest, function(other) {
        return _.indexOf(other, item) >= 0;
      });
    });
  };

  // Take the difference between one array and another.
  // Only the elements present in just the first array will remain.
  _.difference = function(array, other) {
    return _.filter(array, function(value){ return !_.include(other, value); });
  };

  // Zip together multiple lists into a single array -- elements that share
  // an index go together.
  _.zip = function() {
    var args = slice.call(arguments);
    var length = _.max(_.pluck(args, 'length'));
    var results = new Array(length);
    for (var i = 0; i < length; i++) results[i] = _.pluck(args, "" + i);
    return results;
  };

  // If the browser doesn't supply us with indexOf (I'm looking at you, **MSIE**),
  // we need this function. Return the position of the first occurrence of an
  // item in an array, or -1 if the item is not included in the array.
  // Delegates to **ECMAScript 5**'s native `indexOf` if available.
  // If the array is large and already in sort order, pass `true`
  // for **isSorted** to use binary search.
  _.indexOf = function(array, item, isSorted) {
    if (array == null) return -1;
    var i, l;
    if (isSorted) {
      i = _.sortedIndex(array, item);
      return array[i] === item ? i : -1;
    }
    if (nativeIndexOf && array.indexOf === nativeIndexOf) return array.indexOf(item);
    for (i = 0, l = array.length; i < l; i++) if (array[i] === item) return i;
    return -1;
  };


  // Delegates to **ECMAScript 5**'s native `lastIndexOf` if available.
  _.lastIndexOf = function(array, item) {
    if (array == null) return -1;
    if (nativeLastIndexOf && array.lastIndexOf === nativeLastIndexOf) return array.lastIndexOf(item);
    var i = array.length;
    while (i--) if (array[i] === item) return i;
    return -1;
  };

  // Generate an integer Array containing an arithmetic progression. A port of
  // the native Python `range()` function. See
  // [the Python documentation](http://docs.python.org/library/functions.html#range).
  _.range = function(start, stop, step) {
    if (arguments.length <= 1) {
      stop = start || 0;
      start = 0;
    }
    step = arguments[2] || 1;

    var len = Math.max(Math.ceil((stop - start) / step), 0);
    var idx = 0;
    var range = new Array(len);

    while(idx < len) {
      range[idx++] = start;
      start += step;
    }

    return range;
  };

  // Function (ahem) Functions
  // ------------------

  // Create a function bound to a given object (assigning `this`, and arguments,
  // optionally). Binding with arguments is also known as `curry`.
  // Delegates to **ECMAScript 5**'s native `Function.bind` if available.
  // We check for `func.bind` first, to fail fast when `func` is undefined.
  _.bind = function(func, obj) {
    if (func.bind === nativeBind && nativeBind) return nativeBind.apply(func, slice.call(arguments, 1));
    var args = slice.call(arguments, 2);
    return function() {
      return func.apply(obj, args.concat(slice.call(arguments)));
    };
  };

  // Bind all of an object's methods to that object. Useful for ensuring that
  // all callbacks defined on an object belong to it.
  _.bindAll = function(obj) {
    var funcs = slice.call(arguments, 1);
    if (funcs.length == 0) funcs = _.functions(obj);
    each(funcs, function(f) { obj[f] = _.bind(obj[f], obj); });
    return obj;
  };

  // Memoize an expensive function by storing its results.
  _.memoize = function(func, hasher) {
    var memo = {};
    hasher || (hasher = _.identity);
    return function() {
      var key = hasher.apply(this, arguments);
      return hasOwnProperty.call(memo, key) ? memo[key] : (memo[key] = func.apply(this, arguments));
    };
  };

  // Delays a function for the given number of milliseconds, and then calls
  // it with the arguments supplied.
  _.delay = function(func, wait) {
    var args = slice.call(arguments, 2);
    return setTimeout(function(){ return func.apply(func, args); }, wait);
  };

  // Defers a function, scheduling it to run after the current call stack has
  // cleared.
  _.defer = function(func) {
    return _.delay.apply(_, [func, 1].concat(slice.call(arguments, 1)));
  };

  // Internal function used to implement `_.throttle` and `_.debounce`.
  var limit = function(func, wait, debounce) {
    var timeout;
    return function() {
      var context = this, args = arguments;
      var throttler = function() {
        timeout = null;
        func.apply(context, args);
      };
      if (debounce) clearTimeout(timeout);
      if (debounce || !timeout) timeout = setTimeout(throttler, wait);
    };
  };

  // Returns a function, that, when invoked, will only be triggered at most once
  // during a given window of time.
  _.throttle = function(func, wait) {
    return limit(func, wait, false);
  };

  // Returns a function, that, as long as it continues to be invoked, will not
  // be triggered. The function will be called after it stops being called for
  // N milliseconds.
  _.debounce = function(func, wait) {
    return limit(func, wait, true);
  };

  // Returns a function that will be executed at most one time, no matter how
  // often you call it. Useful for lazy initialization.
  _.once = function(func) {
    var ran = false, memo;
    return function() {
      if (ran) return memo;
      ran = true;
      return memo = func.apply(this, arguments);
    };
  };

  // Returns the first function passed as an argument to the second,
  // allowing you to adjust arguments, run code before and after, and
  // conditionally execute the original function.
  _.wrap = function(func, wrapper) {
    return function() {
      var args = [func].concat(slice.call(arguments));
      return wrapper.apply(this, args);
    };
  };

  // Returns a function that is the composition of a list of functions, each
  // consuming the return value of the function that follows.
  _.compose = function() {
    var funcs = slice.call(arguments);
    return function() {
      var args = slice.call(arguments);
      for (var i = funcs.length - 1; i >= 0; i--) {
        args = [funcs[i].apply(this, args)];
      }
      return args[0];
    };
  };

  // Returns a function that will only be executed after being called N times.
  _.after = function(times, func) {
    return function() {
      if (--times < 1) { return func.apply(this, arguments); }
    };
  };


  // Object Functions
  // ----------------

  // Retrieve the names of an object's properties.
  // Delegates to **ECMAScript 5**'s native `Object.keys`
  _.keys = nativeKeys || function(obj) {
    if (obj !== Object(obj)) throw new TypeError('Invalid object');
    var keys = [];
    for (var key in obj) if (hasOwnProperty.call(obj, key)) keys[keys.length] = key;
    return keys;
  };

  // Retrieve the values of an object's properties.
  _.values = function(obj) {
    return _.map(obj, _.identity);
  };

  // Return a sorted list of the function names available on the object.
  // Aliased as `methods`
  _.functions = _.methods = function(obj) {
    var names = [];
    for (var key in obj) {
      if (_.isFunction(obj[key])) names.push(key);
    }
    return names.sort();
  };

  // Extend a given object with all the properties in passed-in object(s).
  _.extend = function(obj) {
    each(slice.call(arguments, 1), function(source) {
      for (var prop in source) {
        if (source[prop] !== void 0) obj[prop] = source[prop];
      }
    });
    return obj;
  };

  // Fill in a given object with default properties.
  _.defaults = function(obj) {
    each(slice.call(arguments, 1), function(source) {
      for (var prop in source) {
        if (obj[prop] == null) obj[prop] = source[prop];
      }
    });
    return obj;
  };

  // Create a (shallow-cloned) duplicate of an object.
  _.clone = function(obj) {
    return _.isArray(obj) ? obj.slice() : _.extend({}, obj);
  };

  // Invokes interceptor with the obj, and then returns obj.
  // The primary purpose of this method is to "tap into" a method chain, in
  // order to perform operations on intermediate results within the chain.
  _.tap = function(obj, interceptor) {
    interceptor(obj);
    return obj;
  };

  // Perform a deep comparison to check if two objects are equal.
  _.isEqual = function(a, b) {
    // Check object identity.
    if (a === b) return true;
    // Different types?
    var atype = typeof(a), btype = typeof(b);
    if (atype != btype) return false;
    // Basic equality test (watch out for coercions).
    if (a == b) return true;
    // One is falsy and the other truthy.
    if ((!a && b) || (a && !b)) return false;
    // Unwrap any wrapped objects.
    if (a._chain) a = a._wrapped;
    if (b._chain) b = b._wrapped;
    // One of them implements an isEqual()?
    if (a.isEqual) return a.isEqual(b);
    if (b.isEqual) return b.isEqual(a);
    // Check dates' integer values.
    if (_.isDate(a) && _.isDate(b)) return a.getTime() === b.getTime();
    // Both are NaN?
    if (_.isNaN(a) && _.isNaN(b)) return false;
    // Compare regular expressions.
    if (_.isRegExp(a) && _.isRegExp(b))
      return a.source     === b.source &&
             a.global     === b.global &&
             a.ignoreCase === b.ignoreCase &&
             a.multiline  === b.multiline;
    // If a is not an object by this point, we can't handle it.
    if (atype !== 'object') return false;
    // Check for different array lengths before comparing contents.
    if (a.length && (a.length !== b.length)) return false;
    // Nothing else worked, deep compare the contents.
    var aKeys = _.keys(a), bKeys = _.keys(b);
    // Different object sizes?
    if (aKeys.length != bKeys.length) return false;
    // Recursive comparison of contents.
    for (var key in a) if (!(key in b) || !_.isEqual(a[key], b[key])) return false;
    return true;
  };

  // Is a given array or object empty?
  _.isEmpty = function(obj) {
    if (_.isArray(obj) || _.isString(obj)) return obj.length === 0;
    for (var key in obj) if (hasOwnProperty.call(obj, key)) return false;
    return true;
  };

  // Is a given value a DOM element?
  _.isElement = function(obj) {
    return !!(obj && obj.nodeType == 1);
  };

  // Is a given value an array?
  // Delegates to ECMA5's native Array.isArray
  _.isArray = nativeIsArray || function(obj) {
    return toString.call(obj) === '[object Array]';
  };

  // Is a given variable an object?
  _.isObject = function(obj) {
    return obj === Object(obj);
  };

  // Is a given variable an arguments object?
  _.isArguments = function(obj) {
    return !!(obj && hasOwnProperty.call(obj, 'callee'));
  };

  // Is a given value a function?
  _.isFunction = function(obj) {
    return !!(obj && obj.constructor && obj.call && obj.apply);
  };

  // Is a given value a string?
  _.isString = function(obj) {
    return !!(obj === '' || (obj && obj.charCodeAt && obj.substr));
  };

  // Is a given value a number?
  _.isNumber = function(obj) {
    return !!(obj === 0 || (obj && obj.toExponential && obj.toFixed));
  };

  // Is the given value `NaN`? `NaN` happens to be the only value in JavaScript
  // that does not equal itself.
  _.isNaN = function(obj) {
    return obj !== obj;
  };

  // Is a given value a boolean?
  _.isBoolean = function(obj) {
    return obj === true || obj === false;
  };

  // Is a given value a date?
  _.isDate = function(obj) {
    return !!(obj && obj.getTimezoneOffset && obj.setUTCFullYear);
  };

  // Is the given value a regular expression?
  _.isRegExp = function(obj) {
    return !!(obj && obj.test && obj.exec && (obj.ignoreCase || obj.ignoreCase === false));
  };

  // Is a given value equal to null?
  _.isNull = function(obj) {
    return obj === null;
  };

  // Is a given variable undefined?
  _.isUndefined = function(obj) {
    return obj === void 0;
  };

  // Utility Functions
  // -----------------

  // Run Underscore.js in *noConflict* mode, returning the `_` variable to its
  // previous owner. Returns a reference to the Underscore object.
  _.noConflict = function() {
    root._ = previousUnderscore;
    return this;
  };

  // Keep the identity function around for default iterators.
  _.identity = function(value) {
    return value;
  };

  // Run a function **n** times.
  _.times = function (n, iterator, context) {
    for (var i = 0; i < n; i++) iterator.call(context, i);
  };

  // Add your own custom functions to the Underscore object, ensuring that
  // they're correctly added to the OOP wrapper as well.
  _.mixin = function(obj) {
    each(_.functions(obj), function(name){
      addToWrapper(name, _[name] = obj[name]);
    });
  };

  // Generate a unique integer id (unique within the entire client session).
  // Useful for temporary DOM ids.
  var idCounter = 0;
  _.uniqueId = function(prefix) {
    var id = idCounter++;
    return prefix ? prefix + id : id;
  };

  // By default, Underscore uses ERB-style template delimiters, change the
  // following template settings to use alternative delimiters.
  _.templateSettings = {
    evaluate    : /<%([\s\S]+?)%>/g,
    interpolate : /<%=([\s\S]+?)%>/g
  };

  // JavaScript micro-templating, similar to John Resig's implementation.
  // Underscore templating handles arbitrary delimiters, preserves whitespace,
  // and correctly escapes quotes within interpolated code.
  _.template = function(str, data) {
    var c  = _.templateSettings;
    var tmpl = 'var __p=[],print=function(){__p.push.apply(__p,arguments);};' +
      'with(obj||{}){__p.push(\'' +
      str.replace(/\\/g, '\\\\')
         .replace(/'/g, "\\'")
         .replace(c.interpolate, function(match, code) {
           return "'," + code.replace(/\\'/g, "'") + ",'";
         })
         .replace(c.evaluate || null, function(match, code) {
           return "');" + code.replace(/\\'/g, "'")
                              .replace(/[\r\n\t]/g, ' ') + "__p.push('";
         })
         .replace(/\r/g, '\\r')
         .replace(/\n/g, '\\n')
         .replace(/\t/g, '\\t')
         + "');}return __p.join('');";
    var func = new Function('obj', tmpl);
    return data ? func(data) : func;
  };

  // The OOP Wrapper
  // ---------------

  // If Underscore is called as a function, it returns a wrapped object that
  // can be used OO-style. This wrapper holds altered versions of all the
  // underscore functions. Wrapped objects may be chained.
  var wrapper = function(obj) { this._wrapped = obj; };

  // Expose `wrapper.prototype` as `_.prototype`
  _.prototype = wrapper.prototype;

  // Helper function to continue chaining intermediate results.
  var result = function(obj, chain) {
    return chain ? _(obj).chain() : obj;
  };

  // A method to easily add functions to the OOP wrapper.
  var addToWrapper = function(name, func) {
    wrapper.prototype[name] = function() {
      var args = slice.call(arguments);
      unshift.call(args, this._wrapped);
      return result(func.apply(_, args), this._chain);
    };
  };

  // Add all of the Underscore functions to the wrapper object.
  _.mixin(_);

  // Add all mutator Array functions to the wrapper.
  each(['pop', 'push', 'reverse', 'shift', 'sort', 'splice', 'unshift'], function(name) {
    var method = ArrayProto[name];
    wrapper.prototype[name] = function() {
      method.apply(this._wrapped, arguments);
      return result(this._wrapped, this._chain);
    };
  });

  // Add all accessor Array functions to the wrapper.
  each(['concat', 'join', 'slice'], function(name) {
    var method = ArrayProto[name];
    wrapper.prototype[name] = function() {
      return result(method.apply(this._wrapped, arguments), this._chain);
    };
  });

  // Start chaining a wrapped Underscore object.
  wrapper.prototype.chain = function() {
    this._chain = true;
    return this;
  };

  // Extracts the result from a wrapped and chained object.
  wrapper.prototype.value = function() {
    return this._wrapped;
  };

})();
//     Backbone.js 0.5.1
//     (c) 2010 Jeremy Ashkenas, DocumentCloud Inc.
//     Backbone may be freely distributed under the MIT license.
//     For all details and documentation:
//     http://documentcloud.github.com/backbone

(function(){

  // Initial Setup
  // -------------

  // Save a reference to the global object.
  var root = this;

  // Save the previous value of the `Backbone` variable.
  var previousBackbone = root.Backbone;

  // The top-level namespace. All public Backbone classes and modules will
  // be attached to this. Exported for both CommonJS and the browser.
  var Backbone;
  if (typeof exports !== 'undefined') {
    Backbone = exports;
  } else {
    Backbone = root.Backbone = {};
  }

  // Current version of the library. Keep in sync with `package.json`.
  Backbone.VERSION = '0.5.1';

  // Require Underscore, if we're on the server, and it's not already present.
  var _ = root._;
  if (!_ && (typeof require !== 'undefined')) _ = require('underscore')._;

  // For Backbone's purposes, jQuery or Zepto owns the `$` variable.
  var $ = root.jQuery || root.Zepto;

  // Runs Backbone.js in *noConflict* mode, returning the `Backbone` variable
  // to its previous owner. Returns a reference to this Backbone object.
  Backbone.noConflict = function() {
    root.Backbone = previousBackbone;
    return this;
  };

  // Turn on `emulateHTTP` to use support legacy HTTP servers. Setting this option will
  // fake `"PUT"` and `"DELETE"` requests via the `_method` parameter and set a
  // `X-Http-Method-Override` header.
  Backbone.emulateHTTP = false;

  // Turn on `emulateJSON` to support legacy servers that can't deal with direct
  // `application/json` requests ... will encode the body as
  // `application/x-www-form-urlencoded` instead and will send the model in a
  // form param named `model`.
  Backbone.emulateJSON = false;

  // Backbone.Events
  // -----------------

  // A module that can be mixed in to *any object* in order to provide it with
  // custom events. You may `bind` or `unbind` a callback function to an event;
  // `trigger`-ing an event fires all callbacks in succession.
  //
  //     var object = {};
  //     _.extend(object, Backbone.Events);
  //     object.bind('expand', function(){ alert('expanded'); });
  //     object.trigger('expand');
  //
  Backbone.Events = {

    // Bind an event, specified by a string name, `ev`, to a `callback` function.
    // Passing `"all"` will bind the callback to all events fired.
    bind : function(ev, callback) {
      var calls = this._callbacks || (this._callbacks = {});
      var list  = calls[ev] || (calls[ev] = []);
      list.push(callback);
      return this;
    },

    // Remove one or many callbacks. If `callback` is null, removes all
    // callbacks for the event. If `ev` is null, removes all bound callbacks
    // for all events.
    unbind : function(ev, callback) {
      var calls;
      if (!ev) {
        this._callbacks = {};
      } else if (calls = this._callbacks) {
        if (!callback) {
          calls[ev] = [];
        } else {
          var list = calls[ev];
          if (!list) return this;
          for (var i = 0, l = list.length; i < l; i++) {
            if (callback === list[i]) {
              list[i] = null;
              break;
            }
          }
        }
      }
      return this;
    },

    // Trigger an event, firing all bound callbacks. Callbacks are passed the
    // same arguments as `trigger` is, apart from the event name.
    // Listening for `"all"` passes the true event name as the first argument.
    trigger : function(eventName) {
      var list, calls, ev, callback, args;
      var both = 2;
      if (!(calls = this._callbacks)) return this;
      while (both--) {
        ev = both ? eventName : 'all';
        if (list = calls[ev]) {
          for (var i = 0, l = list.length; i < l; i++) {
            if (!(callback = list[i])) {
              list.splice(i, 1); i--; l--;
            } else {
              args = both ? Array.prototype.slice.call(arguments, 1) : arguments;
              callback.apply(this, args);
            }
          }
        }
      }
      return this;
    }

  };

  // Backbone.Model
  // --------------

  // Create a new model, with defined attributes. A client id (`cid`)
  // is automatically generated and assigned for you.
  Backbone.Model = function(attributes, options) {
    var defaults;
    attributes || (attributes = {});
    if (defaults = this.defaults) {
      if (_.isFunction(defaults)) defaults = defaults();
      attributes = _.extend({}, defaults, attributes);
    }
    this.attributes = {};
    this._escapedAttributes = {};
    this.cid = _.uniqueId('c');
    this.set(attributes, {silent : true});
    this._changed = false;
    this._previousAttributes = _.clone(this.attributes);
    if (options && options.collection) this.collection = options.collection;
    this.initialize(attributes, options);
  };

  // Attach all inheritable methods to the Model prototype.
  _.extend(Backbone.Model.prototype, Backbone.Events, {

    // A snapshot of the model's previous attributes, taken immediately
    // after the last `"change"` event was fired.
    _previousAttributes : null,

    // Has the item been changed since the last `"change"` event?
    _changed : false,

    // The default name for the JSON `id` attribute is `"id"`. MongoDB and
    // CouchDB users may want to set this to `"_id"`.
    idAttribute : 'id',

    // Initialize is an empty function by default. Override it with your own
    // initialization logic.
    initialize : function(){},

    // Return a copy of the model's `attributes` object.
    toJSON : function() {
      return _.clone(this.attributes);
    },

    // Get the value of an attribute.
    get : function(attr) {
      return this.attributes[attr];
    },

    // Get the HTML-escaped value of an attribute.
    escape : function(attr) {
      var html;
      if (html = this._escapedAttributes[attr]) return html;
      var val = this.attributes[attr];
      return this._escapedAttributes[attr] = escapeHTML(val == null ? '' : '' + val);
    },

    // Returns `true` if the attribute contains a value that is not null
    // or undefined.
    has : function(attr) {
      return this.attributes[attr] != null;
    },

    // Set a hash of model attributes on the object, firing `"change"` unless you
    // choose to silence it.
    set : function(attrs, options) {

      // Extract attributes and options.
      options || (options = {});
      if (!attrs) return this;
      if (attrs.attributes) attrs = attrs.attributes;
      var now = this.attributes, escaped = this._escapedAttributes;

      // Run validation.
      if (!options.silent && this.validate && !this._performValidation(attrs, options)) return false;

      // Check for changes of `id`.
      if (this.idAttribute in attrs) this.id = attrs[this.idAttribute];

      // We're about to start triggering change events.
      var alreadyChanging = this._changing;
      this._changing = true;

      // Update attributes.
      for (var attr in attrs) {
        var val = attrs[attr];
        if (!_.isEqual(now[attr], val)) {
          now[attr] = val;
          delete escaped[attr];
          this._changed = true;
          if (!options.silent) this.trigger('change:' + attr, this, val, options);
        }
      }

      // Fire the `"change"` event, if the model has been changed.
      if (!alreadyChanging && !options.silent && this._changed) this.change(options);
      this._changing = false;
      return this;
    },

    // Remove an attribute from the model, firing `"change"` unless you choose
    // to silence it. `unset` is a noop if the attribute doesn't exist.
    unset : function(attr, options) {
      if (!(attr in this.attributes)) return this;
      options || (options = {});
      var value = this.attributes[attr];

      // Run validation.
      var validObj = {};
      validObj[attr] = void 0;
      if (!options.silent && this.validate && !this._performValidation(validObj, options)) return false;

      // Remove the attribute.
      delete this.attributes[attr];
      delete this._escapedAttributes[attr];
      if (attr == this.idAttribute) delete this.id;
      this._changed = true;
      if (!options.silent) {
        this.trigger('change:' + attr, this, void 0, options);
        this.change(options);
      }
      return this;
    },

    // Clear all attributes on the model, firing `"change"` unless you choose
    // to silence it.
    clear : function(options) {
      options || (options = {});
      var attr;
      var old = this.attributes;

      // Run validation.
      var validObj = {};
      for (attr in old) validObj[attr] = void 0;
      if (!options.silent && this.validate && !this._performValidation(validObj, options)) return false;

      this.attributes = {};
      this._escapedAttributes = {};
      this._changed = true;
      if (!options.silent) {
        for (attr in old) {
          this.trigger('change:' + attr, this, void 0, options);
        }
        this.change(options);
      }
      return this;
    },

    // Fetch the model from the server. If the server's representation of the
    // model differs from its current attributes, they will be overriden,
    // triggering a `"change"` event.
    fetch : function(options) {
      options || (options = {});
      var model = this;
      var success = options.success;
      options.success = function(resp, status, xhr) {
        if (!model.set(model.parse(resp, xhr), options)) return false;
        if (success) success(model, resp);
      };
      options.error = wrapError(options.error, model, options);
      return (this.sync || Backbone.sync).call(this, 'read', this, options);
    },

    // Set a hash of model attributes, and sync the model to the server.
    // If the server returns an attributes hash that differs, the model's
    // state will be `set` again.
    save : function(attrs, options) {
      options || (options = {});
      if (attrs && !this.set(attrs, options)) return false;
      var model = this;
      var success = options.success;
      options.success = function(resp, status, xhr) {
        if (!model.set(model.parse(resp, xhr), options)) return false;
        if (success) success(model, resp, xhr);
      };
      options.error = wrapError(options.error, model, options);
      var method = this.isNew() ? 'create' : 'update';
      return (this.sync || Backbone.sync).call(this, method, this, options);
    },

    // Destroy this model on the server if it was already persisted. Upon success, the model is removed
    // from its collection, if it has one.
    destroy : function(options) {
      options || (options = {});
      if (this.isNew()) return this.trigger('destroy', this, this.collection, options);
      var model = this;
      var success = options.success;
      options.success = function(resp) {
        model.trigger('destroy', model, model.collection, options);
        if (success) success(model, resp);
      };
      options.error = wrapError(options.error, model, options);
      return (this.sync || Backbone.sync).call(this, 'delete', this, options);
    },

    // Default URL for the model's representation on the server -- if you're
    // using Backbone's restful methods, override this to change the endpoint
    // that will be called.
    url : function() {
      var base = getUrl(this.collection) || this.urlRoot || urlError();
      if (this.isNew()) return base;
      return base + (base.charAt(base.length - 1) == '/' ? '' : '/') + encodeURIComponent(this.id);
    },

    // **parse** converts a response into the hash of attributes to be `set` on
    // the model. The default implementation is just to pass the response along.
    parse : function(resp, xhr) {
      return resp;
    },

    // Create a new model with identical attributes to this one.
    clone : function() {
      return new this.constructor(this);
    },

    // A model is new if it has never been saved to the server, and lacks an id.
    isNew : function() {
      return this.id == null;
    },

    // Call this method to manually fire a `change` event for this model.
    // Calling this will cause all objects observing the model to update.
    change : function(options) {
      this.trigger('change', this, options);
      this._previousAttributes = _.clone(this.attributes);
      this._changed = false;
    },

    // Determine if the model has changed since the last `"change"` event.
    // If you specify an attribute name, determine if that attribute has changed.
    hasChanged : function(attr) {
      if (attr) return this._previousAttributes[attr] != this.attributes[attr];
      return this._changed;
    },

    // Return an object containing all the attributes that have changed, or false
    // if there are no changed attributes. Useful for determining what parts of a
    // view need to be updated and/or what attributes need to be persisted to
    // the server.
    changedAttributes : function(now) {
      now || (now = this.attributes);
      var old = this._previousAttributes;
      var changed = false;
      for (var attr in now) {
        if (!_.isEqual(old[attr], now[attr])) {
          changed = changed || {};
          changed[attr] = now[attr];
        }
      }
      return changed;
    },

    // Get the previous value of an attribute, recorded at the time the last
    // `"change"` event was fired.
    previous : function(attr) {
      if (!attr || !this._previousAttributes) return null;
      return this._previousAttributes[attr];
    },

    // Get all of the attributes of the model at the time of the previous
    // `"change"` event.
    previousAttributes : function() {
      return _.clone(this._previousAttributes);
    },

    // Run validation against a set of incoming attributes, returning `true`
    // if all is well. If a specific `error` callback has been passed,
    // call that instead of firing the general `"error"` event.
    _performValidation : function(attrs, options) {
      var error = this.validate(attrs);
      if (error) {
        if (options.error) {
          options.error(this, error, options);
        } else {
          this.trigger('error', this, error, options);
        }
        return false;
      }
      return true;
    }

  });

  // Backbone.Collection
  // -------------------

  // Provides a standard collection class for our sets of models, ordered
  // or unordered. If a `comparator` is specified, the Collection will maintain
  // its models in sort order, as they're added and removed.
  Backbone.Collection = function(models, options) {
    options || (options = {});
    if (options.comparator) this.comparator = options.comparator;
    _.bindAll(this, '_onModelEvent', '_removeReference');
    this._reset();
    if (models) this.reset(models, {silent: true});
    this.initialize.apply(this, arguments);
  };

  // Define the Collection's inheritable methods.
  _.extend(Backbone.Collection.prototype, Backbone.Events, {

    // The default model for a collection is just a **Backbone.Model**.
    // This should be overridden in most cases.
    model : Backbone.Model,

    // Initialize is an empty function by default. Override it with your own
    // initialization logic.
    initialize : function(){},

    // The JSON representation of a Collection is an array of the
    // models' attributes.
    toJSON : function() {
      return this.map(function(model){ return model.toJSON(); });
    },

    // Add a model, or list of models to the set. Pass **silent** to avoid
    // firing the `added` event for every new model.
    add : function(models, options) {
      if (_.isArray(models)) {
        for (var i = 0, l = models.length; i < l; i++) {
          this._add(models[i], options);
        }
      } else {
        this._add(models, options);
      }
      return this;
    },

    // Remove a model, or a list of models from the set. Pass silent to avoid
    // firing the `removed` event for every model removed.
    remove : function(models, options) {
      if (_.isArray(models)) {
        for (var i = 0, l = models.length; i < l; i++) {
          this._remove(models[i], options);
        }
      } else {
        this._remove(models, options);
      }
      return this;
    },

    // Get a model from the set by id.
    get : function(id) {
      if (id == null) return null;
      return this._byId[id.id != null ? id.id : id];
    },

    // Get a model from the set by client id.
    getByCid : function(cid) {
      return cid && this._byCid[cid.cid || cid];
    },

    // Get the model at the given index.
    at: function(index) {
      return this.models[index];
    },

    // Force the collection to re-sort itself. You don't need to call this under normal
    // circumstances, as the set will maintain sort order as each item is added.
    sort : function(options) {
      options || (options = {});
      if (!this.comparator) throw new Error('Cannot sort a set without a comparator');
      this.models = this.sortBy(this.comparator);
      if (!options.silent) this.trigger('reset', this, options);
      return this;
    },

    // Pluck an attribute from each model in the collection.
    pluck : function(attr) {
      return _.map(this.models, function(model){ return model.get(attr); });
    },

    // When you have more items than you want to add or remove individually,
    // you can reset the entire set with a new list of models, without firing
    // any `added` or `removed` events. Fires `reset` when finished.
    reset : function(models, options) {
      models  || (models = []);
      options || (options = {});
      this.each(this._removeReference);
      this._reset();
      this.add(models, {silent: true});
      if (!options.silent) this.trigger('reset', this, options);
      return this;
    },

    // Fetch the default set of models for this collection, resetting the
    // collection when they arrive. If `add: true` is passed, appends the
    // models to the collection instead of resetting.
    fetch : function(options) {
      options || (options = {});
      var collection = this;
      var success = options.success;
      options.success = function(resp, status, xhr) {
        collection[options.add ? 'add' : 'reset'](collection.parse(resp, xhr), options);
        if (success) success(collection, resp);
      };
      options.error = wrapError(options.error, collection, options);
      return (this.sync || Backbone.sync).call(this, 'read', this, options);
    },

    // Create a new instance of a model in this collection. After the model
    // has been created on the server, it will be added to the collection.
    // Returns the model, or 'false' if validation on a new model fails.
    create : function(model, options) {
      var coll = this;
      options || (options = {});
      model = this._prepareModel(model, options);
      if (!model) return false;
      var success = options.success;
      options.success = function(nextModel, resp, xhr) {
        coll.add(nextModel, options);
        if (success) success(nextModel, resp, xhr);
      };
      model.save(null, options);
      return model;
    },

    // **parse** converts a response into a list of models to be added to the
    // collection. The default implementation is just to pass it through.
    parse : function(resp, xhr) {
      return resp;
    },

    // Proxy to _'s chain. Can't be proxied the same way the rest of the
    // underscore methods are proxied because it relies on the underscore
    // constructor.
    chain: function () {
      return _(this.models).chain();
    },

    // Reset all internal state. Called when the collection is reset.
    _reset : function(options) {
      this.length = 0;
      this.models = [];
      this._byId  = {};
      this._byCid = {};
    },

    // Prepare a model to be added to this collection
    _prepareModel: function(model, options) {
      if (!(model instanceof Backbone.Model)) {
        var attrs = model;
        model = new this.model(attrs, {collection: this});
        if (model.validate && !model._performValidation(attrs, options)) model = false;
      } else if (!model.collection) {
        model.collection = this;
      }
      return model;
    },

    // Internal implementation of adding a single model to the set, updating
    // hash indexes for `id` and `cid` lookups.
    // Returns the model, or 'false' if validation on a new model fails.
    _add : function(model, options) {
      options || (options = {});
      model = this._prepareModel(model, options);
      if (!model) return false;
      var already = this.getByCid(model) || this.get(model);
      if (already) throw new Error(["Can't add the same model to a set twice", already.id]);
      this._byId[model.id] = model;
      this._byCid[model.cid] = model;
      var index = options.at != null ? options.at :
                  this.comparator ? this.sortedIndex(model, this.comparator) :
                  this.length;
      this.models.splice(index, 0, model);
      model.bind('all', this._onModelEvent);
      this.length++;
      if (!options.silent) model.trigger('add', model, this, options);
      return model;
    },

    // Internal implementation of removing a single model from the set, updating
    // hash indexes for `id` and `cid` lookups.
    _remove : function(model, options) {
      options || (options = {});
      model = this.getByCid(model) || this.get(model);
      if (!model) return null;
      delete this._byId[model.id];
      delete this._byCid[model.cid];
      this.models.splice(this.indexOf(model), 1);
      this.length--;
      if (!options.silent) model.trigger('remove', model, this, options);
      this._removeReference(model);
      return model;
    },

    // Internal method to remove a model's ties to a collection.
    _removeReference : function(model) {
      if (this == model.collection) {
        delete model.collection;
      }
      model.unbind('all', this._onModelEvent);
    },

    // Internal method called every time a model in the set fires an event.
    // Sets need to update their indexes when models change ids. All other
    // events simply proxy through. "add" and "remove" events that originate
    // in other collections are ignored.
    _onModelEvent : function(ev, model, collection, options) {
      if ((ev == 'add' || ev == 'remove') && collection != this) return;
      if (ev == 'destroy') {
        this._remove(model, options);
      }
      if (model && ev === 'change:' + model.idAttribute) {
        delete this._byId[model.previous(model.idAttribute)];
        this._byId[model.id] = model;
      }
      this.trigger.apply(this, arguments);
    }

  });

  // Underscore methods that we want to implement on the Collection.
  var methods = ['forEach', 'each', 'map', 'reduce', 'reduceRight', 'find', 'detect',
    'filter', 'select', 'reject', 'every', 'all', 'some', 'any', 'include',
    'contains', 'invoke', 'max', 'min', 'sortBy', 'sortedIndex', 'toArray', 'size',
    'first', 'rest', 'last', 'without', 'indexOf', 'lastIndexOf', 'isEmpty'];

  // Mix in each Underscore method as a proxy to `Collection#models`.
  _.each(methods, function(method) {
    Backbone.Collection.prototype[method] = function() {
      return _[method].apply(_, [this.models].concat(_.toArray(arguments)));
    };
  });

  // Backbone.Router
  // -------------------

  // Routers map faux-URLs to actions, and fire events when routes are
  // matched. Creating a new one sets its `routes` hash, if not set statically.
  Backbone.Router = function(options) {
    options || (options = {});
    if (options.routes) this.routes = options.routes;
    this._bindRoutes();
    this.initialize.apply(this, arguments);
  };

  // Cached regular expressions for matching named param parts and splatted
  // parts of route strings.
  var namedParam    = /:([\w\d]+)/g;
  var splatParam    = /\*([\w\d]+)/g;
  var escapeRegExp  = /[-[\]{}()+?.,\\^$|#\s]/g;

  // Set up all inheritable **Backbone.Router** properties and methods.
  _.extend(Backbone.Router.prototype, Backbone.Events, {

    // Initialize is an empty function by default. Override it with your own
    // initialization logic.
    initialize : function(){},

    // Manually bind a single named route to a callback. For example:
    //
    //     this.route('search/:query/p:num', 'search', function(query, num) {
    //       ...
    //     });
    //
    route : function(route, name, callback) {
      Backbone.history || (Backbone.history = new Backbone.History);
      if (!_.isRegExp(route)) route = this._routeToRegExp(route);
      Backbone.history.route(route, _.bind(function(fragment) {
        var args = this._extractParameters(route, fragment);
        callback.apply(this, args);
        this.trigger.apply(this, ['route:' + name].concat(args));
      }, this));
    },

    // Simple proxy to `Backbone.history` to save a fragment into the history.
    navigate : function(fragment, triggerRoute) {
      Backbone.history.navigate(fragment, triggerRoute);
    },

    // Bind all defined routes to `Backbone.history`. We have to reverse the
    // order of the routes here to support behavior where the most general
    // routes can be defined at the bottom of the route map.
    _bindRoutes : function() {
      if (!this.routes) return;
      var routes = [];
      for (var route in this.routes) {
        routes.unshift([route, this.routes[route]]);
      }
      for (var i = 0, l = routes.length; i < l; i++) {
        this.route(routes[i][0], routes[i][1], this[routes[i][1]]);
      }
    },

    // Convert a route string into a regular expression, suitable for matching
    // against the current location hash.
    _routeToRegExp : function(route) {
      route = route.replace(escapeRegExp, "\\$&")
                   .replace(namedParam, "([^\/]*)")
                   .replace(splatParam, "(.*?)");
      return new RegExp('^' + route + '$');
    },

    // Given a route, and a URL fragment that it matches, return the array of
    // extracted parameters.
    _extractParameters : function(route, fragment) {
      return route.exec(fragment).slice(1);
    }

  });

  // Backbone.History
  // ----------------

  // Handles cross-browser history management, based on URL fragments. If the
  // browser does not support `onhashchange`, falls back to polling.
  Backbone.History = function() {
    this.handlers = [];
    _.bindAll(this, 'checkUrl');
  };

  // Cached regex for cleaning hashes.
  var hashStrip = /^#*/;

  // Cached regex for detecting MSIE.
  var isExplorer = /msie [\w.]+/;

  // Has the history handling already been started?
  var historyStarted = false;

  // Set up all inheritable **Backbone.History** properties and methods.
  _.extend(Backbone.History.prototype, {

    // The default interval to poll for hash changes, if necessary, is
    // twenty times a second.
    interval: 50,

    // Get the cross-browser normalized URL fragment, either from the URL,
    // the hash, or the override.
    getFragment : function(fragment, forcePushState) {
      if (fragment == null) {
        if (this._hasPushState || forcePushState) {
          fragment = window.location.pathname;
          var search = window.location.search;
          if (search) fragment += search;
          if (fragment.indexOf(this.options.root) == 0) fragment = fragment.substr(this.options.root.length);
        } else {
          fragment = window.location.hash;
        }
      }
      return fragment.replace(hashStrip, '');
    },

    // Start the hash change handling, returning `true` if the current URL matches
    // an existing route, and `false` otherwise.
    start : function(options) {

      // Figure out the initial configuration. Do we need an iframe?
      // Is pushState desired ... is it available?
      if (historyStarted) throw new Error("Backbone.history has already been started");
      this.options          = _.extend({}, {root: '/'}, this.options, options);
      this._wantsPushState  = !!this.options.pushState;
      this._hasPushState    = !!(this.options.pushState && window.history && window.history.pushState);
      var fragment          = this.getFragment();
      var docMode           = document.documentMode;
      var oldIE             = (isExplorer.exec(navigator.userAgent.toLowerCase()) && (!docMode || docMode <= 7));
      if (oldIE) {
        this.iframe = $('<iframe src="javascript:0" tabindex="-1" />').hide().appendTo('body')[0].contentWindow;
        this.navigate(fragment);
      }

      // Depending on whether we're using pushState or hashes, and whether
      // 'onhashchange' is supported, determine how we check the URL state.
      if (this._hasPushState) {
        $(window).bind('popstate', this.checkUrl);
      } else if ('onhashchange' in window && !oldIE) {
        $(window).bind('hashchange', this.checkUrl);
      } else {
        setInterval(this.checkUrl, this.interval);
      }

      // Determine if we need to change the base url, for a pushState link
      // opened by a non-pushState browser.
      this.fragment = fragment;
      historyStarted = true;
      var loc = window.location;
      var atRoot  = loc.pathname == this.options.root;
      if (this._wantsPushState && !this._hasPushState && !atRoot) {
        this.fragment = this.getFragment(null, true);
        window.location.replace(this.options.root + '#' + this.fragment);
      } else if (this._wantsPushState && this._hasPushState && atRoot && loc.hash) {
        this.fragment = loc.hash.replace(hashStrip, '');
        window.history.replaceState({}, document.title, loc.protocol + '//' + loc.host + this.options.root + this.fragment);
      }
      return this.loadUrl();
    },

    // Add a route to be tested when the fragment changes. Routes added later may
    // override previous routes.
    route : function(route, callback) {
      this.handlers.unshift({route : route, callback : callback});
    },

    // Checks the current URL to see if it has changed, and if it has,
    // calls `loadUrl`, normalizing across the hidden iframe.
    checkUrl : function(e) {
      var current = this.getFragment();
      if (current == this.fragment && this.iframe) current = this.getFragment(this.iframe.location.hash);
      if (current == this.fragment || current == decodeURIComponent(this.fragment)) return false;
      if (this.iframe) this.navigate(current);
      this.loadUrl() || this.loadUrl(window.location.hash);
    },

    // Attempt to load the current URL fragment. If a route succeeds with a
    // match, returns `true`. If no defined routes matches the fragment,
    // returns `false`.
    loadUrl : function(fragmentOverride) {
      var fragment = this.fragment = this.getFragment(fragmentOverride);
      var matched = _.any(this.handlers, function(handler) {
        if (handler.route.test(fragment)) {
          handler.callback(fragment);
          return true;
        }
      });
      return matched;
    },

    // Save a fragment into the hash history. You are responsible for properly
    // URL-encoding the fragment in advance. This does not trigger
    // a `hashchange` event.
    navigate : function(fragment, triggerRoute) {
      var frag = (fragment || '').replace(hashStrip, '');
      if (this.fragment == frag || this.fragment == decodeURIComponent(frag)) return;
      if (this._hasPushState) {
        var loc = window.location;
        if (frag.indexOf(this.options.root) != 0) frag = this.options.root + frag;
        this.fragment = frag;
        window.history.pushState({}, document.title, loc.protocol + '//' + loc.host + frag);
      } else {
        window.location.hash = this.fragment = frag;
        if (this.iframe && (frag != this.getFragment(this.iframe.location.hash))) {
          this.iframe.document.open().close();
          this.iframe.location.hash = frag;
        }
      }
      if (triggerRoute) this.loadUrl(fragment);
    }

  });

  // Backbone.View
  // -------------

  // Creating a Backbone.View creates its initial element outside of the DOM,
  // if an existing element is not provided...
  Backbone.View = function(options) {
    this.cid = _.uniqueId('view');
    this._configure(options || {});
    this._ensureElement();
    this.delegateEvents();
    this.initialize.apply(this, arguments);
  };

  // Element lookup, scoped to DOM elements within the current view.
  // This should be prefered to global lookups, if you're dealing with
  // a specific view.
  var selectorDelegate = function(selector) {
    return $(selector, this.el);
  };

  // Cached regex to split keys for `delegate`.
  var eventSplitter = /^(\S+)\s*(.*)$/;

  // List of view options to be merged as properties.
  var viewOptions = ['model', 'collection', 'el', 'id', 'attributes', 'className', 'tagName'];

  // Set up all inheritable **Backbone.View** properties and methods.
  _.extend(Backbone.View.prototype, Backbone.Events, {

    // The default `tagName` of a View's element is `"div"`.
    tagName : 'div',

    // Attach the `selectorDelegate` function as the `$` property.
    $       : selectorDelegate,

    // Initialize is an empty function by default. Override it with your own
    // initialization logic.
    initialize : function(){},

    // **render** is the core function that your view should override, in order
    // to populate its element (`this.el`), with the appropriate HTML. The
    // convention is for **render** to always return `this`.
    render : function() {
      return this;
    },

    // Remove this view from the DOM. Note that the view isn't present in the
    // DOM by default, so calling this method may be a no-op.
    remove : function() {
      $(this.el).remove();
      return this;
    },

    // For small amounts of DOM Elements, where a full-blown template isn't
    // needed, use **make** to manufacture elements, one at a time.
    //
    //     var el = this.make('li', {'class': 'row'}, this.model.escape('title'));
    //
    make : function(tagName, attributes, content) {
      var el = document.createElement(tagName);
      if (attributes) $(el).attr(attributes);
      if (content) $(el).html(content);
      return el;
    },

    // Set callbacks, where `this.callbacks` is a hash of
    //
    // *{"event selector": "callback"}*
    //
    //     {
    //       'mousedown .title':  'edit',
    //       'click .button':     'save'
    //     }
    //
    // pairs. Callbacks will be bound to the view, with `this` set properly.
    // Uses event delegation for efficiency.
    // Omitting the selector binds the event to `this.el`.
    // This only works for delegate-able events: not `focus`, `blur`, and
    // not `change`, `submit`, and `reset` in Internet Explorer.
    delegateEvents : function(events) {
      if (!(events || (events = this.events))) return;
      $(this.el).unbind('.delegateEvents' + this.cid);
      for (var key in events) {
        var method = this[events[key]];
        if (!method) throw new Error('Event "' + events[key] + '" does not exist');
        var match = key.match(eventSplitter);
        var eventName = match[1], selector = match[2];
        method = _.bind(method, this);
        eventName += '.delegateEvents' + this.cid;
        if (selector === '') {
          $(this.el).bind(eventName, method);
        } else {
          $(this.el).delegate(selector, eventName, method);
        }
      }
    },

    // Performs the initial configuration of a View with a set of options.
    // Keys with special meaning *(model, collection, id, className)*, are
    // attached directly to the view.
    _configure : function(options) {
      if (this.options) options = _.extend({}, this.options, options);
      for (var i = 0, l = viewOptions.length; i < l; i++) {
        var attr = viewOptions[i];
        if (options[attr]) this[attr] = options[attr];
      }
      this.options = options;
    },

    // Ensure that the View has a DOM element to render into.
    // If `this.el` is a string, pass it through `$()`, take the first
    // matching element, and re-assign it to `el`. Otherwise, create
    // an element from the `id`, `className` and `tagName` proeprties.
    _ensureElement : function() {
      if (!this.el) {
        var attrs = this.attributes || {};
        if (this.id) attrs.id = this.id;
        if (this.className) attrs['class'] = this.className;
        this.el = this.make(this.tagName, attrs);
      } else if (_.isString(this.el)) {
        this.el = $(this.el).get(0);
      }
    }

  });

  // The self-propagating extend function that Backbone classes use.
  var extend = function (protoProps, classProps) {
    var child = inherits(this, protoProps, classProps);
    child.extend = this.extend;
    return child;
  };

  // Set up inheritance for the model, collection, and view.
  Backbone.Model.extend = Backbone.Collection.extend =
    Backbone.Router.extend = Backbone.View.extend = extend;

  // Map from CRUD to HTTP for our default `Backbone.sync` implementation.
  var methodMap = {
    'create': 'POST',
    'update': 'PUT',
    'delete': 'DELETE',
    'read'  : 'GET'
  };

  // Backbone.sync
  // -------------

  // Override this function to change the manner in which Backbone persists
  // models to the server. You will be passed the type of request, and the
  // model in question. By default, uses makes a RESTful Ajax request
  // to the model's `url()`. Some possible customizations could be:
  //
  // * Use `setTimeout` to batch rapid-fire updates into a single request.
  // * Send up the models as XML instead of JSON.
  // * Persist models via WebSockets instead of Ajax.
  //
  // Turn on `Backbone.emulateHTTP` in order to send `PUT` and `DELETE` requests
  // as `POST`, with a `_method` parameter containing the true HTTP method,
  // as well as all requests with the body as `application/x-www-form-urlencoded` instead of
  // `application/json` with the model in a param named `model`.
  // Useful when interfacing with server-side languages like **PHP** that make
  // it difficult to read the body of `PUT` requests.
  Backbone.sync = function(method, model, options) {
    var type = methodMap[method];

    // Default JSON-request options.
    var params = _.extend({
      type:         type,
      dataType:     'json',
      processData:  false
    }, options);

    // Ensure that we have a URL.
    if (!params.url) {
      params.url = getUrl(model) || urlError();
    }

    // Ensure that we have the appropriate request data.
    if (!params.data && model && (method == 'create' || method == 'update')) {
      params.contentType = 'application/json';
      params.data = JSON.stringify(model.toJSON());
    }

    // For older servers, emulate JSON by encoding the request into an HTML-form.
    if (Backbone.emulateJSON) {
      params.contentType = 'application/x-www-form-urlencoded';
      params.processData = true;
      params.data        = params.data ? {model : params.data} : {};
    }

    // For older servers, emulate HTTP by mimicking the HTTP method with `_method`
    // And an `X-HTTP-Method-Override` header.
    if (Backbone.emulateHTTP) {
      if (type === 'PUT' || type === 'DELETE') {
        if (Backbone.emulateJSON) params.data._method = type;
        params.type = 'POST';
        params.beforeSend = function(xhr) {
          xhr.setRequestHeader('X-HTTP-Method-Override', type);
        };
      }
    }

    // Make the request.
    return $.ajax(params);
  };

  // Helpers
  // -------

  // Shared empty constructor function to aid in prototype-chain creation.
  var ctor = function(){};

  // Helper function to correctly set up the prototype chain, for subclasses.
  // Similar to `goog.inherits`, but uses a hash of prototype properties and
  // class properties to be extended.
  var inherits = function(parent, protoProps, staticProps) {
    var child;

    // The constructor function for the new subclass is either defined by you
    // (the "constructor" property in your `extend` definition), or defaulted
    // by us to simply call `super()`.
    if (protoProps && protoProps.hasOwnProperty('constructor')) {
      child = protoProps.constructor;
    } else {
      child = function(){ return parent.apply(this, arguments); };
    }

    // Inherit class (static) properties from parent.
    _.extend(child, parent);

    // Set the prototype chain to inherit from `parent`, without calling
    // `parent`'s constructor function.
    ctor.prototype = parent.prototype;
    child.prototype = new ctor();

    // Add prototype properties (instance properties) to the subclass,
    // if supplied.
    if (protoProps) _.extend(child.prototype, protoProps);

    // Add static properties to the constructor function, if supplied.
    if (staticProps) _.extend(child, staticProps);

    // Correctly set child's `prototype.constructor`.
    child.prototype.constructor = child;

    // Set a convenience property in case the parent's prototype is needed later.
    child.__super__ = parent.prototype;

    return child;
  };

  // Helper function to get a URL from a Model or Collection as a property
  // or as a function.
  var getUrl = function(object) {
    if (!(object && object.url)) return null;
    return _.isFunction(object.url) ? object.url() : object.url;
  };

  // Throw an error when a URL is needed, and none is supplied.
  var urlError = function() {
    throw new Error('A "url" property or function must be specified');
  };

  // Wrap an optional error callback with a fallback error event.
  var wrapError = function(onError, model, options) {
    return function(resp) {
      if (onError) {
        onError(model, resp, options);
      } else {
        model.trigger('error', model, resp, options);
      }
    };
  };

  // Helper function to escape a string for HTML rendering.
  var escapeHTML = function(string) {
    return string.replace(/&(?!\w+;|#\d+;|#x[\da-f]+;)/gi, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#x27').replace(/\//g,'&#x2F;');
  };

}).call(this);
/*
 * timeago: a jQuery plugin, version: 0.9.3 (2011-01-21)
 * @requires jQuery v1.2.3 or later
 *
 * Timeago is a jQuery plugin that makes it easy to support automatically
 * updating fuzzy timestamps (e.g. "4 minutes ago" or "about 1 day ago").
 *
 * For usage and examples, visit:
 * http://timeago.yarp.com/
 *
 * Licensed under the MIT:
 * http://www.opensource.org/licenses/mit-license.php
 *
 * Copyright (c) 2008-2011, Ryan McGeary (ryanonjavascript -[at]- mcgeary [*dot*] org)
 */
(function($) {
  $.timeago = function(timestamp) {
    if (timestamp instanceof Date) {
      return inWords(timestamp);
    } else if (typeof timestamp === "string") {
      return inWords($.timeago.parse(timestamp));
    } else {
      return inWords($.timeago.datetime(timestamp));
    }
  };
  var $t = $.timeago;

  $.extend($.timeago, {
    settings: {
      refreshMillis: 60000,
      allowFuture: false,
      strings: {
        prefixAgo: null,
        prefixFromNow: null,
        suffixAgo: "ago",
        suffixFromNow: "from now",
        seconds: "less than a minute",
        minute: "about a minute",
        minutes: "%d minutes",
        hour: "about an hour",
        hours: "about %d hours",
        day: "a day",
        days: "%d days",
        month: "about a month",
        months: "%d months",
        year: "about a year",
        years: "%d years",
        numbers: []
      }
    },
    inWords: function(distanceMillis) {
      var $l = this.settings.strings;
      var prefix = $l.prefixAgo;
      var suffix = $l.suffixAgo;
      if (this.settings.allowFuture) {
        if (distanceMillis < 0) {
          prefix = $l.prefixFromNow;
          suffix = $l.suffixFromNow;
        }
        distanceMillis = Math.abs(distanceMillis);
      }

      var seconds = distanceMillis / 1000;
      var minutes = seconds / 60;
      var hours = minutes / 60;
      var days = hours / 24;
      var years = days / 365;

      function substitute(stringOrFunction, number) {
        var string = $.isFunction(stringOrFunction) ? stringOrFunction(number, distanceMillis) : stringOrFunction;
        var value = ($l.numbers && $l.numbers[number]) || number;
        return string.replace(/%d/i, value);
      }

      var words = seconds < 45 && substitute($l.seconds, Math.round(seconds)) ||
        seconds < 90 && substitute($l.minute, 1) ||
        minutes < 45 && substitute($l.minutes, Math.round(minutes)) ||
        minutes < 90 && substitute($l.hour, 1) ||
        hours < 24 && substitute($l.hours, Math.round(hours)) ||
        hours < 48 && substitute($l.day, 1) ||
        days < 30 && substitute($l.days, Math.floor(days)) ||
        days < 60 && substitute($l.month, 1) ||
        days < 365 && substitute($l.months, Math.floor(days / 30)) ||
        years < 2 && substitute($l.year, 1) ||
        substitute($l.years, Math.floor(years));

      return $.trim([prefix, words, suffix].join(" "));
    },
    parse: function(iso8601) {
      var s = $.trim(iso8601);
      s = s.replace(/\.\d\d\d+/,""); // remove milliseconds
      s = s.replace(/-/,"/").replace(/-/,"/");
      s = s.replace(/T/," ").replace(/Z/," UTC");
      s = s.replace(/([\+\-]\d\d)\:?(\d\d)/," $1$2"); // -04:00 -> -0400
      return new Date(s);
    },
    datetime: function(elem) {
      // jQuery's `is()` doesn't play well with HTML5 in IE
      var isTime = $(elem).get(0).tagName.toLowerCase() === "time"; // $(elem).is("time");
      var iso8601 = isTime ? $(elem).attr("datetime") : $(elem).attr("title");
      return $t.parse(iso8601);
    }
  });

  $.fn.timeago = function() {
    var self = this;
    self.each(refresh);

    var $s = $t.settings;
    if ($s.refreshMillis > 0) {
      setInterval(function() { self.each(refresh); }, $s.refreshMillis);
    }
    return self;
  };

  function refresh() {
    var data = prepareData(this);
    if (!isNaN(data.datetime)) {
      $(this).text(inWords(data.datetime));
    }
    return this;
  }

  function prepareData(element) {
    element = $(element);
    if (!element.data("timeago")) {
      element.data("timeago", { datetime: $t.datetime(element) });
      var text = $.trim(element.text());
      if (text.length > 0) {
        element.attr("title", text);
      }
    }
    return element.data("timeago");
  }

  function inWords(date) {
    return $t.inWords(distance(date));
  }

  function distance(date) {
    return (new Date().getTime() - date.getTime());
  }

  // fix for IE6 suckage
  document.createElement("abbr");
  document.createElement("time");
}(jQuery));

/*	SWFObject v2.2 <http://code.google.com/p/swfobject/> 
	is released under the MIT License <http://www.opensource.org/licenses/mit-license.php> 
*/
var swfobject=function(){var D="undefined",r="object",S="Shockwave Flash",W="ShockwaveFlash.ShockwaveFlash",q="application/x-shockwave-flash",R="SWFObjectExprInst",x="onreadystatechange",O=window,j=document,t=navigator,T=false,U=[h],o=[],N=[],I=[],l,Q,E,B,J=false,a=false,n,G,m=true,M=function(){var aa=typeof j.getElementById!=D&&typeof j.getElementsByTagName!=D&&typeof j.createElement!=D,ah=t.userAgent.toLowerCase(),Y=t.platform.toLowerCase(),ae=Y?/win/.test(Y):/win/.test(ah),ac=Y?/mac/.test(Y):/mac/.test(ah),af=/webkit/.test(ah)?parseFloat(ah.replace(/^.*webkit\/(\d+(\.\d+)?).*$/,"$1")):false,X=!+"\v1",ag=[0,0,0],ab=null;if(typeof t.plugins!=D&&typeof t.plugins[S]==r){ab=t.plugins[S].description;if(ab&&!(typeof t.mimeTypes!=D&&t.mimeTypes[q]&&!t.mimeTypes[q].enabledPlugin)){T=true;X=false;ab=ab.replace(/^.*\s+(\S+\s+\S+$)/,"$1");ag[0]=parseInt(ab.replace(/^(.*)\..*$/,"$1"),10);ag[1]=parseInt(ab.replace(/^.*\.(.*)\s.*$/,"$1"),10);ag[2]=/[a-zA-Z]/.test(ab)?parseInt(ab.replace(/^.*[a-zA-Z]+(.*)$/,"$1"),10):0}}else{if(typeof O.ActiveXObject!=D){try{var ad=new ActiveXObject(W);if(ad){ab=ad.GetVariable("$version");if(ab){X=true;ab=ab.split(" ")[1].split(",");ag=[parseInt(ab[0],10),parseInt(ab[1],10),parseInt(ab[2],10)]}}}catch(Z){}}}return{w3:aa,pv:ag,wk:af,ie:X,win:ae,mac:ac}}(),k=function(){if(!M.w3){return}if((typeof j.readyState!=D&&j.readyState=="complete")||(typeof j.readyState==D&&(j.getElementsByTagName("body")[0]||j.body))){f()}if(!J){if(typeof j.addEventListener!=D){j.addEventListener("DOMContentLoaded",f,false)}if(M.ie&&M.win){j.attachEvent(x,function(){if(j.readyState=="complete"){j.detachEvent(x,arguments.callee);f()}});if(O==top){(function(){if(J){return}try{j.documentElement.doScroll("left")}catch(X){setTimeout(arguments.callee,0);return}f()})()}}if(M.wk){(function(){if(J){return}if(!/loaded|complete/.test(j.readyState)){setTimeout(arguments.callee,0);return}f()})()}s(f)}}();function f(){if(J){return}try{var Z=j.getElementsByTagName("body")[0].appendChild(C("span"));Z.parentNode.removeChild(Z)}catch(aa){return}J=true;var X=U.length;for(var Y=0;Y<X;Y++){U[Y]()}}function K(X){if(J){X()}else{U[U.length]=X}}function s(Y){if(typeof O.addEventListener!=D){O.addEventListener("load",Y,false)}else{if(typeof j.addEventListener!=D){j.addEventListener("load",Y,false)}else{if(typeof O.attachEvent!=D){i(O,"onload",Y)}else{if(typeof O.onload=="function"){var X=O.onload;O.onload=function(){X();Y()}}else{O.onload=Y}}}}}function h(){if(T){V()}else{H()}}function V(){var X=j.getElementsByTagName("body")[0];var aa=C(r);aa.setAttribute("type",q);var Z=X.appendChild(aa);if(Z){var Y=0;(function(){if(typeof Z.GetVariable!=D){var ab=Z.GetVariable("$version");if(ab){ab=ab.split(" ")[1].split(",");M.pv=[parseInt(ab[0],10),parseInt(ab[1],10),parseInt(ab[2],10)]}}else{if(Y<10){Y++;setTimeout(arguments.callee,10);return}}X.removeChild(aa);Z=null;H()})()}else{H()}}function H(){var ag=o.length;if(ag>0){for(var af=0;af<ag;af++){var Y=o[af].id;var ab=o[af].callbackFn;var aa={success:false,id:Y};if(M.pv[0]>0){var ae=c(Y);if(ae){if(F(o[af].swfVersion)&&!(M.wk&&M.wk<312)){w(Y,true);if(ab){aa.success=true;aa.ref=z(Y);ab(aa)}}else{if(o[af].expressInstall&&A()){var ai={};ai.data=o[af].expressInstall;ai.width=ae.getAttribute("width")||"0";ai.height=ae.getAttribute("height")||"0";if(ae.getAttribute("class")){ai.styleclass=ae.getAttribute("class")}if(ae.getAttribute("align")){ai.align=ae.getAttribute("align")}var ah={};var X=ae.getElementsByTagName("param");var ac=X.length;for(var ad=0;ad<ac;ad++){if(X[ad].getAttribute("name").toLowerCase()!="movie"){ah[X[ad].getAttribute("name")]=X[ad].getAttribute("value")}}P(ai,ah,Y,ab)}else{p(ae);if(ab){ab(aa)}}}}}else{w(Y,true);if(ab){var Z=z(Y);if(Z&&typeof Z.SetVariable!=D){aa.success=true;aa.ref=Z}ab(aa)}}}}}function z(aa){var X=null;var Y=c(aa);if(Y&&Y.nodeName=="OBJECT"){if(typeof Y.SetVariable!=D){X=Y}else{var Z=Y.getElementsByTagName(r)[0];if(Z){X=Z}}}return X}function A(){return !a&&F("6.0.65")&&(M.win||M.mac)&&!(M.wk&&M.wk<312)}function P(aa,ab,X,Z){a=true;E=Z||null;B={success:false,id:X};var ae=c(X);if(ae){if(ae.nodeName=="OBJECT"){l=g(ae);Q=null}else{l=ae;Q=X}aa.id=R;if(typeof aa.width==D||(!/%$/.test(aa.width)&&parseInt(aa.width,10)<310)){aa.width="310"}if(typeof aa.height==D||(!/%$/.test(aa.height)&&parseInt(aa.height,10)<137)){aa.height="137"}j.title=j.title.slice(0,47)+" - Flash Player Installation";var ad=M.ie&&M.win?"ActiveX":"PlugIn",ac="MMredirectURL="+O.location.toString().replace(/&/g,"%26")+"&MMplayerType="+ad+"&MMdoctitle="+j.title;if(typeof ab.flashvars!=D){ab.flashvars+="&"+ac}else{ab.flashvars=ac}if(M.ie&&M.win&&ae.readyState!=4){var Y=C("div");X+="SWFObjectNew";Y.setAttribute("id",X);ae.parentNode.insertBefore(Y,ae);ae.style.display="none";(function(){if(ae.readyState==4){ae.parentNode.removeChild(ae)}else{setTimeout(arguments.callee,10)}})()}u(aa,ab,X)}}function p(Y){if(M.ie&&M.win&&Y.readyState!=4){var X=C("div");Y.parentNode.insertBefore(X,Y);X.parentNode.replaceChild(g(Y),X);Y.style.display="none";(function(){if(Y.readyState==4){Y.parentNode.removeChild(Y)}else{setTimeout(arguments.callee,10)}})()}else{Y.parentNode.replaceChild(g(Y),Y)}}function g(ab){var aa=C("div");if(M.win&&M.ie){aa.innerHTML=ab.innerHTML}else{var Y=ab.getElementsByTagName(r)[0];if(Y){var ad=Y.childNodes;if(ad){var X=ad.length;for(var Z=0;Z<X;Z++){if(!(ad[Z].nodeType==1&&ad[Z].nodeName=="PARAM")&&!(ad[Z].nodeType==8)){aa.appendChild(ad[Z].cloneNode(true))}}}}}return aa}function u(ai,ag,Y){var X,aa=c(Y);if(M.wk&&M.wk<312){return X}if(aa){if(typeof ai.id==D){ai.id=Y}if(M.ie&&M.win){var ah="";for(var ae in ai){if(ai[ae]!=Object.prototype[ae]){if(ae.toLowerCase()=="data"){ag.movie=ai[ae]}else{if(ae.toLowerCase()=="styleclass"){ah+=' class="'+ai[ae]+'"'}else{if(ae.toLowerCase()!="classid"){ah+=" "+ae+'="'+ai[ae]+'"'}}}}}var af="";for(var ad in ag){if(ag[ad]!=Object.prototype[ad]){af+='<param name="'+ad+'" value="'+ag[ad]+'" />'}}aa.outerHTML='<object classid="clsid:D27CDB6E-AE6D-11cf-96B8-444553540000"'+ah+">"+af+"</object>";N[N.length]=ai.id;X=c(ai.id)}else{var Z=C(r);Z.setAttribute("type",q);for(var ac in ai){if(ai[ac]!=Object.prototype[ac]){if(ac.toLowerCase()=="styleclass"){Z.setAttribute("class",ai[ac])}else{if(ac.toLowerCase()!="classid"){Z.setAttribute(ac,ai[ac])}}}}for(var ab in ag){if(ag[ab]!=Object.prototype[ab]&&ab.toLowerCase()!="movie"){e(Z,ab,ag[ab])}}aa.parentNode.replaceChild(Z,aa);X=Z}}return X}function e(Z,X,Y){var aa=C("param");aa.setAttribute("name",X);aa.setAttribute("value",Y);Z.appendChild(aa)}function y(Y){var X=c(Y);if(X&&X.nodeName=="OBJECT"){if(M.ie&&M.win){X.style.display="none";(function(){if(X.readyState==4){b(Y)}else{setTimeout(arguments.callee,10)}})()}else{X.parentNode.removeChild(X)}}}function b(Z){var Y=c(Z);if(Y){for(var X in Y){if(typeof Y[X]=="function"){Y[X]=null}}Y.parentNode.removeChild(Y)}}function c(Z){var X=null;try{X=j.getElementById(Z)}catch(Y){}return X}function C(X){return j.createElement(X)}function i(Z,X,Y){Z.attachEvent(X,Y);I[I.length]=[Z,X,Y]}function F(Z){var Y=M.pv,X=Z.split(".");X[0]=parseInt(X[0],10);X[1]=parseInt(X[1],10)||0;X[2]=parseInt(X[2],10)||0;return(Y[0]>X[0]||(Y[0]==X[0]&&Y[1]>X[1])||(Y[0]==X[0]&&Y[1]==X[1]&&Y[2]>=X[2]))?true:false}function v(ac,Y,ad,ab){if(M.ie&&M.mac){return}var aa=j.getElementsByTagName("head")[0];if(!aa){return}var X=(ad&&typeof ad=="string")?ad:"screen";if(ab){n=null;G=null}if(!n||G!=X){var Z=C("style");Z.setAttribute("type","text/css");Z.setAttribute("media",X);n=aa.appendChild(Z);if(M.ie&&M.win&&typeof j.styleSheets!=D&&j.styleSheets.length>0){n=j.styleSheets[j.styleSheets.length-1]}G=X}if(M.ie&&M.win){if(n&&typeof n.addRule==r){n.addRule(ac,Y)}}else{if(n&&typeof j.createTextNode!=D){n.appendChild(j.createTextNode(ac+" {"+Y+"}"))}}}function w(Z,X){if(!m){return}var Y=X?"visible":"hidden";if(J&&c(Z)){c(Z).style.visibility=Y}else{v("#"+Z,"visibility:"+Y)}}function L(Y){var Z=/[\\\"<>\.;]/;var X=Z.exec(Y)!=null;return X&&typeof encodeURIComponent!=D?encodeURIComponent(Y):Y}var d=function(){if(M.ie&&M.win){window.attachEvent("onunload",function(){var ac=I.length;for(var ab=0;ab<ac;ab++){I[ab][0].detachEvent(I[ab][1],I[ab][2])}var Z=N.length;for(var aa=0;aa<Z;aa++){y(N[aa])}for(var Y in M){M[Y]=null}M=null;for(var X in swfobject){swfobject[X]=null}swfobject=null})}}();return{registerObject:function(ab,X,aa,Z){if(M.w3&&ab&&X){var Y={};Y.id=ab;Y.swfVersion=X;Y.expressInstall=aa;Y.callbackFn=Z;o[o.length]=Y;w(ab,false)}else{if(Z){Z({success:false,id:ab})}}},getObjectById:function(X){if(M.w3){return z(X)}},embedSWF:function(ab,ah,ae,ag,Y,aa,Z,ad,af,ac){var X={success:false,id:ah};if(M.w3&&!(M.wk&&M.wk<312)&&ab&&ah&&ae&&ag&&Y){w(ah,false);K(function(){ae+="";ag+="";var aj={};if(af&&typeof af===r){for(var al in af){aj[al]=af[al]}}aj.data=ab;aj.width=ae;aj.height=ag;var am={};if(ad&&typeof ad===r){for(var ak in ad){am[ak]=ad[ak]}}if(Z&&typeof Z===r){for(var ai in Z){if(typeof am.flashvars!=D){am.flashvars+="&"+ai+"="+Z[ai]}else{am.flashvars=ai+"="+Z[ai]}}}if(F(Y)){var an=u(aj,am,ah);if(aj.id==ah){w(ah,true)}X.success=true;X.ref=an}else{if(aa&&A()){aj.data=aa;P(aj,am,ah,ac);return}else{w(ah,true)}}if(ac){ac(X)}})}else{if(ac){ac(X)}}},switchOffAutoHideShow:function(){m=false},ua:M,getFlashPlayerVersion:function(){return{major:M.pv[0],minor:M.pv[1],release:M.pv[2]}},hasFlashPlayerVersion:F,createSWF:function(Z,Y,X){if(M.w3){return u(Z,Y,X)}else{return undefined}},showExpressInstall:function(Z,aa,X,Y){if(M.w3&&A()){P(Z,aa,X,Y)}},removeSWF:function(X){if(M.w3){y(X)}},createCSS:function(aa,Z,Y,X){if(M.w3){v(aa,Z,Y,X)}},addDomLoadEvent:K,addLoadEvent:s,getQueryParamValue:function(aa){var Z=j.location.search||j.location.hash;if(Z){if(/\?/.test(Z)){Z=Z.split("?")[1]}if(aa==null){return L(Z)}var Y=Z.split("&");for(var X=0;X<Y.length;X++){if(Y[X].substring(0,Y[X].indexOf("="))==aa){return L(Y[X].substring((Y[X].indexOf("=")+1)))}}}return""},expressInstallCallback:function(){if(a){var X=c(R);if(X&&l){X.parentNode.replaceChild(l,X);if(Q){w(Q,true);if(M.ie&&M.win){l.style.display="block"}}if(E){E(B)}}a=false}}}}();

/*
Uploadify v2.1.4
Release Date: November 8, 2010

Copyright (c) 2010 Ronnie Garcia, Travis Nickels

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
*/

if(jQuery)(
	function(jQuery){
		jQuery.extend(jQuery.fn,{
			uploadify:function(options) {
				jQuery(this).each(function(){
					var settings = jQuery.extend({
					id              : jQuery(this).attr('id'), // The ID of the object being Uploadified
					uploader        : 'uploadify.swf', // The path to the uploadify swf file
					script          : 'uploadify.php', // The path to the uploadify backend upload script
					expressInstall  : null, // The path to the express install swf file
					folder          : '', // The path to the upload folder
					height          : 30, // The height of the flash button
					width           : 120, // The width of the flash button
					cancelImg       : 'cancel.png', // The path to the cancel image for the default file queue item container
					wmode           : 'opaque', // The wmode of the flash file
					scriptAccess    : 'sameDomain', // Set to "always" to allow script access across domains
					fileDataName    : 'Filedata', // The name of the file collection object in the backend upload script
					method          : 'POST', // The method for sending variables to the backend upload script
					queueSizeLimit  : 999, // The maximum size of the file queue
					simUploadLimit  : 1, // The number of simultaneous uploads allowed
					queueID         : false, // The optional ID of the queue container
					displayData     : 'percentage', // Set to "speed" to show the upload speed in the default queue item
					removeCompleted : true, // Set to true if you want the queue items to be removed when a file is done uploading
					onInit          : function() {}, // Function to run when uploadify is initialized
					onSelect        : function() {}, // Function to run when a file is selected
					onSelectOnce    : function() {}, // Function to run once when files are added to the queue
					onQueueFull     : function() {}, // Function to run when the queue reaches capacity
					onCheck         : function() {}, // Function to run when script checks for duplicate files on the server
					onCancel        : function() {}, // Function to run when an item is cleared from the queue
					onClearQueue    : function() {}, // Function to run when the queue is manually cleared
					onError         : function() {}, // Function to run when an upload item returns an error
					onProgress      : function() {}, // Function to run each time the upload progress is updated
					onComplete      : function() {}, // Function to run when an upload is completed
					onAllComplete   : function() {}  // Function to run when all uploads are completed
				}, options);
				jQuery(this).data('settings',settings);
				var pagePath = location.pathname;
				pagePath = pagePath.split('/');
				pagePath.pop();
				pagePath = pagePath.join('/') + '/';
				var data = {};
				data.uploadifyID = settings.id;
				data.pagepath = pagePath;
				if (settings.buttonImg) data.buttonImg = escape(settings.buttonImg);
				if (settings.buttonText) data.buttonText = escape(settings.buttonText);
				if (settings.rollover) data.rollover = true;
				data.script = settings.script;
				data.folder = escape(settings.folder);
				if (settings.scriptData) {
					var scriptDataString = '';
					for (var name in settings.scriptData) {
						scriptDataString += '&' + name + '=' + settings.scriptData[name];
					}
					data.scriptData = escape(scriptDataString.substr(1));
				}
				data.width          = settings.width;
				data.height         = settings.height;
				data.wmode          = settings.wmode;
				data.method         = settings.method;
				data.queueSizeLimit = settings.queueSizeLimit;
				data.simUploadLimit = settings.simUploadLimit;
				if (settings.hideButton)   data.hideButton   = true;
				if (settings.fileDesc)     data.fileDesc     = settings.fileDesc;
				if (settings.fileExt)      data.fileExt      = settings.fileExt;
				if (settings.multi)        data.multi        = true;
				if (settings.auto)         data.auto         = true;
				if (settings.sizeLimit)    data.sizeLimit    = settings.sizeLimit;
				if (settings.checkScript)  data.checkScript  = settings.checkScript;
				if (settings.fileDataName) data.fileDataName = settings.fileDataName;
				if (settings.queueID)      data.queueID      = settings.queueID;
				if (settings.onInit() !== false) {
					jQuery(this).css('display','none');
					jQuery(this).after('<div id="' + jQuery(this).attr('id') + 'Uploader"></div>');
					swfobject.embedSWF(settings.uploader, settings.id + 'Uploader', settings.width, settings.height, '9.0.24', settings.expressInstall, data, {'quality':'high','wmode':settings.wmode,'allowScriptAccess':settings.scriptAccess},{},function(event) {
						if (typeof(settings.onSWFReady) == 'function' && event.success) settings.onSWFReady();
					});
					if (settings.queueID == false) {
						jQuery("#" + jQuery(this).attr('id') + "Uploader").after('<div id="' + jQuery(this).attr('id') + 'Queue" class="uploadifyQueue"></div>');
					} else {
						jQuery("#" + settings.queueID).addClass('uploadifyQueue');
					}
				}
				if (typeof(settings.onOpen) == 'function') {
					jQuery(this).bind("uploadifyOpen", settings.onOpen);
				}
				jQuery(this).bind("uploadifySelect", {'action': settings.onSelect, 'queueID': settings.queueID}, function(event, ID, fileObj) {
					if (event.data.action(event, ID, fileObj) !== false) {
						var byteSize = Math.round(fileObj.size / 1024 * 100) * .01;
						var suffix = 'KB';
						if (byteSize > 1000) {
							byteSize = Math.round(byteSize *.001 * 100) * .01;
							suffix = 'MB';
						}
						var sizeParts = byteSize.toString().split('.');
						if (sizeParts.length > 1) {
							byteSize = sizeParts[0] + '.' + sizeParts[1].substr(0,2);
						} else {
							byteSize = sizeParts[0];
						}
						if (fileObj.name.length > 20) {
							fileName = fileObj.name.substr(0,20) + '...';
						} else {
							fileName = fileObj.name;
						}
						queue = '#' + jQuery(this).attr('id') + 'Queue';
						if (event.data.queueID) {
							queue = '#' + event.data.queueID;
						}
						jQuery(queue).append('<div id="' + jQuery(this).attr('id') + ID + '" class="uploadifyQueueItem">\
								<div class="cancel">\
									<a href="javascript:jQuery(\'#' + jQuery(this).attr('id') + '\').uploadifyCancel(\'' + ID + '\')"><img src="' + settings.cancelImg + '" border="0" /></a>\
								</div>\
								<span class="fileName">' + fileName + ' (' + byteSize + suffix + ')</span><span class="percentage"></span>\
								<div class="uploadifyProgress">\
									<div id="' + jQuery(this).attr('id') + ID + 'ProgressBar" class="uploadifyProgressBar"><!--Progress Bar--></div>\
								</div>\
							</div>');
					}
				});
				jQuery(this).bind("uploadifySelectOnce", {'action': settings.onSelectOnce}, function(event, data) {
					event.data.action(event, data);
					if (settings.auto) {
						if (settings.checkScript) { 
							jQuery(this).uploadifyUpload(null, false);
						} else {
							jQuery(this).uploadifyUpload(null, true);
						}
					}
				});
				jQuery(this).bind("uploadifyQueueFull", {'action': settings.onQueueFull}, function(event, queueSizeLimit) {
					if (event.data.action(event, queueSizeLimit) !== false) {
						alert('The queue is full.  The max size is ' + queueSizeLimit + '.');
					}
				});
				jQuery(this).bind("uploadifyCheckExist", {'action': settings.onCheck}, function(event, checkScript, fileQueueObj, folder, single) {
					var postData = new Object();
					postData = fileQueueObj;
					postData.folder = (folder.substr(0,1) == '/') ? folder : pagePath + folder;
					if (single) {
						for (var ID in fileQueueObj) {
							var singleFileID = ID;
						}
					}
					jQuery.post(checkScript, postData, function(data) {
						for(var key in data) {
							if (event.data.action(event, data, key) !== false) {
								var replaceFile = confirm("Do you want to replace the file " + data[key] + "?");
								if (!replaceFile) {
									document.getElementById(jQuery(event.target).attr('id') + 'Uploader').cancelFileUpload(key,true,true);
								}
							}
						}
						if (single) {
							document.getElementById(jQuery(event.target).attr('id') + 'Uploader').startFileUpload(singleFileID, true);
						} else {
							document.getElementById(jQuery(event.target).attr('id') + 'Uploader').startFileUpload(null, true);
						}
					}, "json");
				});
				jQuery(this).bind("uploadifyCancel", {'action': settings.onCancel}, function(event, ID, fileObj, data, remove, clearFast) {
					if (event.data.action(event, ID, fileObj, data, clearFast) !== false) {
						if (remove) { 
							var fadeSpeed = (clearFast == true) ? 0 : 250;
							jQuery("#" + jQuery(this).attr('id') + ID).fadeOut(fadeSpeed, function() { jQuery(this).remove() });
						}
					}
				});
				jQuery(this).bind("uploadifyClearQueue", {'action': settings.onClearQueue}, function(event, clearFast) {
					var queueID = (settings.queueID) ? settings.queueID : jQuery(this).attr('id') + 'Queue';
					if (clearFast) {
						jQuery("#" + queueID).find('.uploadifyQueueItem').remove();
					}
					if (event.data.action(event, clearFast) !== false) {
						jQuery("#" + queueID).find('.uploadifyQueueItem').each(function() {
							var index = jQuery('.uploadifyQueueItem').index(this);
							jQuery(this).delay(index * 100).fadeOut(250, function() { jQuery(this).remove() });
						});
					}
				});
				var errorArray = [];
				jQuery(this).bind("uploadifyError", {'action': settings.onError}, function(event, ID, fileObj, errorObj) {
					if (event.data.action(event, ID, fileObj, errorObj) !== false) {
						var fileArray = new Array(ID, fileObj, errorObj);
						errorArray.push(fileArray);
						jQuery("#" + jQuery(this).attr('id') + ID).find('.percentage').text(" - " + errorObj.type + " Error");
						jQuery("#" + jQuery(this).attr('id') + ID).find('.uploadifyProgress').hide();
						jQuery("#" + jQuery(this).attr('id') + ID).addClass('uploadifyError');
					}
				});
				if (typeof(settings.onUpload) == 'function') {
					jQuery(this).bind("uploadifyUpload", settings.onUpload);
				}
				jQuery(this).bind("uploadifyProgress", {'action': settings.onProgress, 'toDisplay': settings.displayData}, function(event, ID, fileObj, data) {
					if (event.data.action(event, ID, fileObj, data) !== false) {
						jQuery("#" + jQuery(this).attr('id') + ID + "ProgressBar").animate({'width': data.percentage + '%'},250,function() {
							if (data.percentage == 100) {
								jQuery(this).closest('.uploadifyProgress').fadeOut(250,function() {jQuery(this).remove()});
							}
						});
						if (event.data.toDisplay == 'percentage') displayData = ' - ' + data.percentage + '%';
						if (event.data.toDisplay == 'speed') displayData = ' - ' + data.speed + 'KB/s';
						if (event.data.toDisplay == null) displayData = ' ';
						jQuery("#" + jQuery(this).attr('id') + ID).find('.percentage').text(displayData);
					}
				});
				jQuery(this).bind("uploadifyComplete", {'action': settings.onComplete}, function(event, ID, fileObj, response, data) {
					if (event.data.action(event, ID, fileObj, unescape(response), data) !== false) {
						jQuery("#" + jQuery(this).attr('id') + ID).find('.percentage').text(' - Completed');
						if (settings.removeCompleted) {
							jQuery("#" + jQuery(event.target).attr('id') + ID).fadeOut(250,function() {jQuery(this).remove()});
						}
						jQuery("#" + jQuery(event.target).attr('id') + ID).addClass('completed');
					}
				});
				if (typeof(settings.onAllComplete) == 'function') {
					jQuery(this).bind("uploadifyAllComplete", {'action': settings.onAllComplete}, function(event, data) {
						if (event.data.action(event, data) !== false) {
							errorArray = [];
						}
					});
				}
			});
		},
		uploadifySettings:function(settingName, settingValue, resetObject) {
			var returnValue = false;
			jQuery(this).each(function() {
				if (settingName == 'scriptData' && settingValue != null) {
					if (resetObject) {
						var scriptData = settingValue;
					} else {
						var scriptData = jQuery.extend(jQuery(this).data('settings').scriptData, settingValue);
					}
					var scriptDataString = '';
					for (var name in scriptData) {
						scriptDataString += '&' + name + '=' + scriptData[name];
					}
					settingValue = escape(scriptDataString.substr(1));
				}
				returnValue = document.getElementById(jQuery(this).attr('id') + 'Uploader').updateSettings(settingName, settingValue);
			});
			if (settingValue == null) {
				if (settingName == 'scriptData') {
					var returnSplit = unescape(returnValue).split('&');
					var returnObj   = new Object();
					for (var i = 0; i < returnSplit.length; i++) {
						var iSplit = returnSplit[i].split('=');
						returnObj[iSplit[0]] = iSplit[1];
					}
					returnValue = returnObj;
				}
			}
			return returnValue;
		},
		uploadifyUpload:function(ID,checkComplete) {
			jQuery(this).each(function() {
				if (!checkComplete) checkComplete = false;
				document.getElementById(jQuery(this).attr('id') + 'Uploader').startFileUpload(ID, checkComplete);
			});
		},
		uploadifyCancel:function(ID) {
			jQuery(this).each(function() {
				document.getElementById(jQuery(this).attr('id') + 'Uploader').cancelFileUpload(ID, true, true, false);
			});
		},
		uploadifyClearQueue:function() {
			jQuery(this).each(function() {
				document.getElementById(jQuery(this).attr('id') + 'Uploader').clearFileUploadQueue(false);
			});
		}
	})
})(jQuery);

String.prototype.padL = function(width,pad) 
{     
  if (!width ||width<1)         
    return this;         
   
  if (!pad) pad=" ";             
   
  var length = width - this.length     
   
  if (length < 1)  
    return this.substr(0,width);      
   
  return (String.repeat(pad,length) + this).substr(0,width);     
}     
String.prototype.padR = function(width,pad) 
{     
   if (!width || width<1)         
     return this;              
    
   if (!pad) pad=" ";     
     
   var length = width - this.length     
    
   if (length < 1) this.substr(0,width);      
     return (this + String.repeat(pad,length)).substr(0,width); 
};

String.repeat = function(chr,count) 
{         
  var str = "";      
  for(var x=0;x<count;x++)  
  { 
    str += chr 
  };      
  return str; 
};

Date.prototype.formatDate = function(format) 
{     
  var date = this;     
  if (!format)       
    format="MM/dd/yyyy";                     
  var month = date.getMonth() + 1;     
  var year = date.getFullYear();          
  format = format.replace("MM",month.toString().padL(2,"0"));    
             
  if (format.indexOf("yyyy") > -1)         
    format = format.replace("yyyy",year.toString());     
  else if (format.indexOf("yy") > -1)         
    format = format.replace("yy",year.toString().substr(2,2));      
   
  format = format.replace("dd",date.getDate().toString().padL(2,"0"));      
  var hours = date.getHours();            
   
  if (format.indexOf("t") > -1)     
  {        
    if (hours > 11)         
      format = format.replace("t","pm")        
    else         
      format = format.replace("t","am")     
  }     
   
  if (format.indexOf("HH") > -1)         
    format = format.replace("HH",hours.toString().padL(2,"0"));     
   
  if (format.indexOf("hh") > -1)  
  {         
    if (hours > 12) hours - 12;         
    if (hours == 0) hours = 12;        
    format = format.replace("hh",hours.toString().padL(2,"0"));             
  }     
   
  if (format.indexOf("mm") > -1)        
    format = format.replace("mm",date.getMinutes().toString().padL(2,"0"));     
   
  if (format.indexOf("ss") > -1)        
    format = format.replace("ss",date.getSeconds().toString().padL(2,"0"));     
   
  return format; 
};

$(function() {
  window._void = function(){};

  window.ContentColumnModel = Backbone.Model.extend({
  });

  window.ContentFacetParamModel = Backbone.Model.extend({
  });

  window.ContentFacetModel = Backbone.Model.extend({
  });

  window.ContentColumnCollection = Backbone.Collection.extend({
    model: ContentColumnModel
  });

  window.ContentFacetParamCollection = Backbone.Collection.extend({
    model: ContentFacetParamModel
  });

  window.ContentFacetCollection = Backbone.Collection.extend({
    model: ContentFacetModel
  });

  window.ContentStoreModel = Backbone.Model.extend({
    defaults: {
    },

    initialize: function() {
      _.bindAll(this, 'read', 'create', 'update');
      ContentStoreModel.__super__.initialize.call(this);
    },

    read: function() {
    },

    create: function () {
    },

    update: function () {
    }
  });

  window.StoreConfigModel = Backbone.Model.extend({
    updateWithNewConfig: function() {
      var me = this;
      var columns = new ContentColumnCollection;
      var schema = eval('('+me.get('schema')+')');
      var table = schema['table'];
      if (table) {
        _.each(table.columns, function(col) {
          col['parentModel'] = me;
          var column = new ContentColumnModel(col);
          var view = new ContentColumnView({model: column});
          columns.add(column);
        });
      }

      this.set({
        newColumn: new ContentColumnView({model: new ContentColumnModel({add: true, parentModel: me})}).model
      });

      var facets = new ContentFacetCollection;
      _.each(schema.facets, function(obj) {
        obj['parentModel'] = me;
        var facet = new ContentFacetModel(obj);
        var params = new ContentFacetParamCollection;
        _.each(obj.params, function(param) {
          param['parentModel'] = facet;
          var p = new ContentFacetParamModel(param);
          var pv = new ContentFacetParamView({model: p});
          params.add(p);
        });
        facet.set({
          params: params
        });
        var view = new ContentFacetView({model: facet});
        facets.add(facet);
      });

      this.set({
        newFacet: new ContentFacetView({model: new ContentFacetModel({add: true, parentModel: me})}).model
      });


      this.set({
        columns: columns,
        facets: facets
      });
    },

    initialize: function() {
      _.bindAll(this, 'updateWithNewConfig');
      StoreConfigModel.__super__.initialize.call(this);
      this.updateWithNewConfig();
    }
  });

  window.StoreConfigCollection = Backbone.Collection.extend({
    model: StoreConfigModel
  });

  window.FileModel = Backbone.Model.extend({
  });

  window.FileCollection = Backbone.Collection.extend({
    model: FileModel
  });

  window.CollabModel = Backbone.Model.extend({
  });

  window.CollabCollection = Backbone.Collection.extend({
    model: CollabModel
  });

  window.CollabItemView = Backbone.View.extend({
    tagName: 'li',

    template: $('#collab-item-tmpl').html(),

    events: {
      'click .remove': 'removeMe',
      'mouseout': 'mouseOut',
      'mouseover': 'mouseOver'
    },

    initialize: function() {
      _.bindAll(this, 'mouseOut', 'mouseOver', 'removeMe', 'render');
      this.model.bind('change', this.render);
      this.model.view = this;
    },

    removeMe: function() {
      var me = this;
      $.post('/store/remove-collab/'+me.options.parentView.options.store.get('name'),
        {username: me.model.get('username')},
        function(res) {
          if (res.ok) {
            var collab = me.options.parentView.collection.get(res.id);
            if (collab) {
              me.options.parentView.collection.remove(collab);
              $(me.el).detach();
            }
          }
          else {
            alert(res.error);
          }
        },
        'json'
      );
    },

    mouseOut: function() {
      this.$('.op').hide();
    },

    mouseOver: function() {
      this.$('.op').show();
    },

    render: function() {
      $(this.el).html($.mustache(this.template, this.model.toJSON()));
      return this;
    }
  });

  window.CollabView = Backbone.View.extend({
    template: $('#collab-tmpl').html(),

    events: {
      'click .add': 'addNew'
    },

    initialize: function() {
      _.bindAll(this, 'addNew', 'render');
    },

    addNew: function() {
      var me = this;

      var username = this.$('.new-collab').val();
      if (username == '') {
        alert('Username is required.');
        return;
      }

      $.post('/store/add-collab/'+me.options.store.get('name'), {username: username}, function(res) {
        if (res.ok) {
          var collab = me.collection.get(res.id);
          if (!collab) {  // new user.
            collab = new CollabModel(res);
            me.collection.add(collab);
            me.render();
          }
        }
        else {
          alert(res.error);
        }
      }, 'json');
    },

    render: function() {
      var me = this;
      if (!this.options.rendered) {
        $(this.el).html($.mustache(this.template, {}));
        this.options.rendered = true;
      }
      
      var itemContainer = this.$('.item-container');

      this.collection.each(function(item) {
        if (!item.view) {
          var view = new CollabItemView({
            model: item
          });
          view.options.parentView = me;
        }
        itemContainer.append(item.view.render().el);
      });

      return this;
    }
  });

  window.ContentStoreCollection = Backbone.Collection.extend({
    model: ContentStoreModel,
    url: '/store/stores/'
  });

  var validateColumn = function(col) {
    var res = {ok: true, msg: 'good'};

    if (!col.name) {
      res.ok = false;
      res.msg = 'Name is required.';
    }

    return res;
  };

  var validateFacet = function(obj) {
    var res = {ok: true, msg: 'good'};

    if (!obj.name) {
      res.ok = false;
      res.msg = 'Name is required.';
    }

    return res;
  };


  window.ContentColumnView = Backbone.View.extend({
    template: $('#content-column-tmpl').html(),

    className: 'content-column-item',

    events: {
      'change .multi': 'multiChanged',
      'change .type': 'typeChanged',
      'click .edit': 'showEditor',
      'click .cancel-edit-column': 'showEditor',
      'click .remove': 'removeMe',
      'click .save-column': 'saveColumn',
      'mouseout': 'mouseOut',
      'mouseover': 'mouseOver'
    },

    initialize: function() {
      _.bindAll(this, 'mouseOut', 'mouseOver', 'showEditor', 'typeChanged', 'multiChanged', 'removeMe', 'saveColumn', 'render');
      this.model.bind('change', this.render);
      this.model.view = this;
    },

    mouseOut: function() {
      this.$('.cell .op').hide();
    },

    mouseOver: function() {
      this.$('.cell .op').show();
    },

    multiChanged: function() {
      if (this.$('.multi').val() == 'true') {
        if ($.trim(this.$('.delimiter').val()) == '') {
          this.$('.delimiter').val(',');
        }
        this.$('.delimiter-container').show();
      }
      else {
        this.$('.delimiter-container').hide();
      }
    },

    removeMe: function() {
      this.model.get('parentModel').get('columns').remove(this.model);
      $(this.el).detach();
    },

    saveColumn: function() {
      var el = $(this.el);
      var obj = {
        name: el.find('.name').val(),
        type: el.find('.type').val(),
        from: el.find('.from').val(),
        delimiter: el.find('.delimiter').val(),
        index: el.find('.index').val(),
        multi: el.find('.multi').val(),
        store: el.find('.store').val(),
        termvector: el.find('.termvector').val()
      };

      switch(obj.type) {
        case 'text':
          obj.index = 'ANALYZED';
          obj.multi = 'false';
          obj.store = 'NO';
          obj.termvector = 'NO';
          break;
      }

      if (obj.multi != 'true') {
        obj.delimiter = '';
      }

      var res = validateColumn(obj);
      if (!res.ok) {
        alert(res.msg);
        return;
      }
      this.model.set(obj);
      this.render();
    },

    showEditor: function() {
      this.$('.editor').toggle();
    },

    typeChanged: function() {
      switch (this.$('.type').val()) {
        case 'text':
          this.$('.multi-container').hide();
          break;
        default:
          this.$('.multi-container').show();
          break;
      }
    },

    render: function() {
      $(this.el).html($.mustache(this.template, this.model.toJSON()));
      this.$('.index').val(this.model.get('index'));
      this.$('.delimiter').val(this.model.get('delimiter'));
      this.$('.multi').val(this.model.get('multi')).change();
      this.$('.type').val(this.model.get('type')).change();
      this.$('.store').val(this.model.get('store'));
      this.$('.termvector').val(this.model.get('termvector'));

      return this;
    }
  });

  window.ContentFacetParamView = Backbone.View.extend({
    template: $('#content-facet-param-tmpl').html(),

    className: 'content-facet-param-item',

    events: {
      'click .remove-param': 'removeMe',
      'click .param-edit': 'showEditor',
    },

    initialize: function() {
      _.bindAll(this, 'showEditor', 'removeMe', 'render');
      this.model.view = this;
    },

    removeMe: function() {
      this.model.get('parentModel').get('params').remove(this.model);
      $(this.el).detach();
    },

    showEditor: function() {
      this.$('.param-editor').toggle();
    },

    render: function() {
      $(this.el).html($.mustache(this.template, this.model.toJSON()));
      return this;
    }
  });

  var validateParam = function(param) {
    var res = {ok: true, msg: 'good'};

    if (!param.name) {
      res.ok = false;
      res.msg = 'Name is required.';
    }

    return res;
  };

  window.ContentFacetView = Backbone.View.extend({
    template: $('#content-facet-tmpl').html(),

    className: 'content-facet-item',

    events: {
      'change .type': 'typeChanged',
      'click .edit': 'showEditor',
      'click .cancel-edit-facet': 'showEditor',
      'click .remove': 'removeMe',
      'click .add-param': 'addParam',
      'click .save-facet': 'saveFacet',
      'mouseout': 'mouseOut',
      'mouseover': 'mouseOver'
    },

    initialize: function() {
      _.bindAll(this, 'mouseOut', 'mouseOver', 'showEditor', 'typeChanged', 'removeMe', 'saveFacet', 'render', 'addParam');
      this.model.view = this;
    },

    mouseOut: function() {
      this.$('.cell .op').hide();
    },

    mouseOver: function() {
      this.$('.cell .op').show();
    },

    removeMe: function() {
      this.model.get('parentModel').get('facets').remove(this.model);
      $(this.el).detach();
    },

    saveFacet: function() {
      var el = $(this.el);
      var obj = {
        name: el.find('.name').val(),
        type: el.find('.type').val(),
        depends: el.find('.depends').val(),
        dynamic: el.find('.dynamic').val(),
      };

      var res = validateFacet(obj);
      if (!res.ok) {
        alert(res.msg);
        return;
      }
      this.model.set(obj);
      this.model.get('parentModel').view.updateConfig();
      this.render();
    },

    typeChanged: function() {
      switch (this.$('.type').val()) {
        case 'path':
        case 'range':
          this.$('.params-container').show();
          break;
        default:
          this.$('.params-container').hide();
          break;
      }
    },

    addParam: function() {
      var obj = {
        name: this.$('.add-new-param .param-name').val(),
        value: this.$('.add-new-param .param-value').val()
      };

      var res = validateParam(obj);
      if (!res.ok) {
        alert(res.msg);
        return;
      }

      obj['parentModel'] = this.model;
      var model = new ContentFacetParamModel(obj);
      var view = new ContentFacetParamView({model: model});
      if (!this.model.get('params'))
        this.model.set({'params': new ContentFacetParamCollection});
      this.model.get('params').add(model);

      var container = this.$('.facet-params');
      container.append(view.render().el);

      this.$('.add-new-param').html(this.$('.add-new-param').html());
    },

    showEditor: function() {
      this.$('.editor').toggle();
    },

    render: function() {
      $(this.el).html($.mustache(this.template, this.model.toJSON()));
      this.$('.type').val(this.model.get('type')).change();

      var container = this.$('.facet-params');
      if (this.model.get('params')) {
        this.model.get('params').each(function(obj) {
          container.append(obj.view.render().el);
        });
      }

      return this;
    }
  });

  window.StoreConfigItemView = Backbone.View.extend({
    template: $('#store-config-item-tmpl').html(),

    className: 'store-config-item',

    events: {
      'click .add-column': 'addColumn',
      'click .add-facet': 'addFacet',
      'click .close-all-sub-tabs': 'closeAllSubTabs',
      'click .save-schema-raw': 'saveSchemaRaw',
      'click .save-store': 'saveSchema',
      'click .save-properties': 'saveProperties',
      'click .save-custom-facets': 'saveCustomFacets',
      'click .save-plugins': 'savePlugins',
      'click .save-extensions': 'saveExtensions',
      'click .save-vm-args': 'saveVMArgs',
      'click .schema': 'showSchema',
      'click .properties': 'showProperties',
      'click .custom_facets': 'showCustomFacets',
      'click .plugins': 'showPlugins',
      'click .extensions': 'showExtensions',
      'click .vm_args': 'showVMArgs',
      'click .do-upload-extensions': 'doUploadExtensions',
      'click .activate': 'activateConfig',
      'click .delete': 'deleteConfig',
      'click .show-raw': 'showRaw',
      'click .show-name-editor': 'showNameEditor',
      'click .save-name': 'saveName',
      'mouseout': 'mouseOut',
      'mouseover': 'mouseOver'
    },

    initialize: function() {
      _.bindAll(this, 'addColumn', 'addFacet', 'closeAllSubTabs', 'mouseOut', 'mouseOver', 'render', 'saveSchemaRaw', 'saveSchema', 'saveProperties', 'saveCustomFacets', 'savePlugins', 'saveExtensions', 'saveVMArgs', 'updateConfig', 'showSchema', 'showProperties', 'showCustomFacets', 'showPlugins', 'showExtensions', 'showVMArgs', 'activateConfig', 'deleteConfig', 'doUploadExtensions', 'showRaw', 'showNameEditor', 'saveName');
      this.model.view = this;
    },

    closeAllSubTabs: function() {
      this.$('.store-sub-tab').hide();
    },

    showNameEditor: function() {
      this.$('.name-display').hide();
      this.$('.name-editor').show();
    },

    saveName: function() {
      var me = this;
      this.model.set({name: this.$('input.config-name').val()});
      $.post('/store/'+me.options.parentView.options.store.get('name')+'/update-name/' + me.model.id + '/', {name: this.model.get('name')}, function(res) {
        if (!res.ok)
          alert(res.error);
        else {
          if (res.name == '')
            me.$('span.config-name').text('NA');
          else
            me.$('span.config-name').text(res.name);

          me.$('.name-display').show();
          me.$('.name-editor').hide();
        }
      }, 'json');
    },

    showSchema: function() {
      this.$('.store-sub-tab').hide();
      this.$('.schema-tab').show();
    },

    showProperties: function() {
      this.$('.store-sub-tab').hide();
      this.$('.properties-tab').show();
    },

    showCustomFacets: function() {
      this.$('.store-sub-tab').hide();
      this.$('.custom_facets-tab').show();
    },

    showPlugins: function() {
      this.$('.store-sub-tab').hide();
      this.$('.plugins-tab').show();
    },

    doUploadExtensions: function() {
      this.$('.upload-extensions').uploadifyUpload();
    },

    showExtensions: function() {
      var me = this;
      this.$('.store-sub-tab').hide();
      this.$('.extensions-tab').show();

      if (!me.options.extensionsView) {
        var extensions = new FileCollection;
        extensions.url = '/store/' + me.options.parentView.options.store.get('name') + '/config/' + me.model.id + '/extensions/';
        var extensionsView = me.options.extensionsView = new FilesView({
          collection: extensions
        });
        extensionsView.options.config = me.model;
        extensions.fetch({
          success: function (obj, res) {
            me.$('.extensions-container').empty().append(extensionsView.render().el);

            // Init uploader:
            _.defer(function() {
              me.$('.upload-extensions').uploadify({
                'uploader': '/static/images/uploadify.swf',
                'script': '/files/upload/',
                'cancelImg': '/static/images/cancel.png',
                'fileExt': '*.jar',
                'fileDesc': 'Jar Files',
                'multi': true,
                'onComplete': function (event, ID, fileObj, resText, data) {
                  var res = eval('('+resText+')');
                  extensions.add(res);
                  extensionsView.render();
                }
              });
              me.$('.do-upload-extensions').show();
            });
          },
          error: function (obj, res) {
            alert('Unable to get extensions from the server.');
          }
        });
      }
    },

    showVMArgs: function() {
      this.$('.store-sub-tab').hide();
      this.$('.vm_args-tab').show();
    },

    activateConfig: function() {
      var me = this;
      var really = confirm("This will activate this config, make it permanent, and your future changes to this config will end up create a new one. Do you really want to continue?")
      if (!really)
        return false;

      $.blockUI({ message: '<h1><img class="indicator" src="/static/images/indicator.gif" /> Activating ' + me.options.parentView.options.store.get('name') + ' ...</h1>' });
      $.getJSON('/store/restart-store/'+me.options.parentView.options.store.get('name') + '/' + me.model.id + '/', function(res) {
        me.options.parentView.options.store.set(res);
        me.options.parentView.options.store.view.options.configView = null;
        me.options.parentView.options.store.view.render();

        $.unblockUI();

        if (!res.ok)
          alert(res.error);
      });
    },

    deleteConfig: function() {
      var me = this;
      var really = confirm("This will delete your config, do you really want to continue?")
      if (!really)
        return false;

      $.getJSON('/store/'+me.options.parentView.options.store.get('name')+'/delete-config/' + me.model.id + '/', function(resp){
        if (resp["ok"]){
          me.options.parentView.collection.remove(me.model);
          $(me.el).remove();
        }
        else{
          alert(resp["msg"]);
        }  
      });
    },

    showRaw: function() {
      this.$('.raw-container').toggle();
    },

    addColumn: function() {
      var addNew = this.$('.add-new-column');
      var obj = {
        name: addNew.find('.name').val(),
        type: addNew.find('.type').val(),
        from: addNew.find('.from').val(),
        delimiter: addNew.find('.delimiter').val(),
        index: addNew.find('.index').val(),
        multi: addNew.find('.multi').val(),
        store: addNew.find('.store').val(),
        termvector: addNew.find('.termvector').val()
      };

      switch(obj.type) {
        case 'text':
          obj.index = 'ANALYZED';
          obj.multi = 'false';
          obj.store = 'NO';
          obj.termvector = 'NO';
          break;
      }

      if (obj.multi != 'true') {
        obj.delimiter = '';
      }

      var res = validateColumn(obj);
      if (!res.ok) {
        alert(res.msg);
        return;
      }
      obj['parentModel'] = this.model;
      var model = new ContentColumnModel(obj);
      var view = new ContentColumnView({model: model});
      this.model.get('columns').add(model);

      var columns = this.$('.columns');
      columns.append(view.render().el);
      this.updateConfig();

      this.model.get('newColumn').view.render();
    },

    addFacet: function() {
      var addNew = this.$('.add-new-facet');
      var obj = {
        name: addNew.find('.name').val(),
        type: addNew.find('.type').val(),
        depends: addNew.find('.depends').val(),
        dynamic: addNew.find('.dynamic').val(),
      };

      var params = new ContentFacetParamCollection();
      if (this.model.get('newFacet').get('params')) {
        params = this.model.get('newFacet').get('params');
        this.model.get('newFacet').set({params: new ContentFacetParamCollection()});
      }

      switch(obj.type) {
        case 'path':
        case 'range':
          break;
        default:
          params = new ContentFacetParamCollection();
          break;
      }

      var res = validateFacet(obj);
      if (!res.ok) {
        alert(res.msg);
        return;
      }
      obj['parentModel'] = this.model;
      var model = new ContentFacetModel(obj);
      model.set({params: params});

      var view = new ContentFacetView({model: model});
      this.model.get('facets').add(model);

      var facets = this.$('.facets');
      facets.append(view.render().el);
      this.updateConfig();

      this.model.get('newFacet').view.render();
    },

    updateConfig: function() {
      var schema = eval('('+this.model.get('schema')+')');
      schema.table.columns = [];
      schema.facets = [];
      this.model.get('columns').each(function(obj) {
        var col = obj.toJSON();
        col.parentModel = {};
        schema.table.columns.push(col);
      });
      this.model.get('facets').each(function(obj) {
        var facet = obj.toJSON();
        facet.parentModel = {};
        if (facet.params) {
          var tmpParams = facet.params;
          facet.params = [];
          tmpParams.each(function(param) {
            var pObj = param.toJSON();
            pObj.parentModel = {};
            facet.params.push(pObj);
          });
        }
        schema.facets.push(facet);
      });
      this.model.set({schema: JSON.stringify(schema)});
      this.$('.raw').val(this.model.get('schema'));
    },

    mouseOut: function() {
      this.$('.store-table .op').hide();
    },

    mouseOver: function() {
      this.$('.store-table .op').show();
    },

    saveSchemaRaw: function() {
      this.model.set({schema: this.$('.raw').val()});

      var me = this;
      $.post('/store/'+me.options.parentView.options.store.get('name')+'/update-schema/' + me.model.id + '/', {schema: this.model.get('schema')}, function(res) {
        if (!res.ok)
          alert(res.error);
        else {
          var config = me.options.parentView.collection.get(res.id);
          if (!config) {  // New config
            config = new StoreConfigModel(res);
            me.options.parentView.collection.add(config, {at: 0});
            me.options.parentView.render();
          }
          else {
            me.model.updateWithNewConfig();
            me.render();
          }
        }
      }, 'json');
    },

    saveSchema: function() {
      this.updateConfig();
      var me = this;
      $.post('/store/'+me.options.parentView.options.store.get('name')+'/update-schema/' + me.model.id + '/', {schema: this.model.get('schema')}, function(res) {
        if (!res.ok)
          alert(res.error);
        else {
          var config = me.options.parentView.collection.get(res.id);
          if (!config) {  // New config
            config = new StoreConfigModel(res);
            me.options.parentView.collection.add(config, {at: 0});
            me.options.parentView.render();
          }
          else {
            me.$('.schema-tab').hide();
          }
        }
      }, 'json');
    },

    saveProperties: function() {
      this.model.set({properties: this.$('.store-sub-tab .properties').val()});

      var me = this;
      $.post('/store/'+me.options.parentView.options.store.get('name')+'/update-properties/' + me.model.id + '/', {properties: this.model.get('properties')}, function(res) {
        if (!res.ok)
          alert(res.error);
        else {
          var config = me.options.parentView.collection.get(res.id);
          if (!config) {  // New config
            config = new StoreConfigModel(res);
            me.options.parentView.collection.add(config, {at: 0});
            me.options.parentView.render();
          }
          else {
          }
          me.$('.properties-tab').hide();
        }
      }, 'json');
    },

    saveCustomFacets: function() {
      this.model.set({custom_facets: this.$('.store-sub-tab .custom_facets').val()});

      var me = this;
      $.post('/store/'+me.options.parentView.options.store.get('name')+'/update-custom-facets/' + me.model.id + '/', {custom_facets: this.model.get('custom_facets')}, function(res) {
        if (!res.ok)
          alert(res.error);
        else {
          var config = me.options.parentView.collection.get(res.id);
          if (!config) {  // New config
            config = new StoreConfigModel(res);
            me.options.parentView.collection.add(config, {at: 0});
            me.options.parentView.render();
          }
          else {
          }
          me.$('.custom_facets-tab').hide();
        }
      }, 'json');
    },

    savePlugins: function() {
      this.model.set({plugins: this.$('.store-sub-tab .plugins').val()});

      var me = this;
      $.post('/store/'+me.options.parentView.options.store.get('name')+'/update-plugins/' + me.model.id + '/', {plugins: this.model.get('plugins')}, function(res) {
        if (!res.ok)
          alert(res.error);
        else {
          var config = me.options.parentView.collection.get(res.id);
          if (!config) {  // New config
            config = new StoreConfigModel(res);
            me.options.parentView.collection.add(config, {at: 0});
            me.options.parentView.render();
          }
          else {
          }
          me.$('.plugins-tab').hide();
        }
      }, 'json');
    },

    saveExtensions: function() {
      var me = this;
      var extensions = [];
      me.options.extensionsView.collection.each(function(obj) {
        extensions.push(obj.id);
      });
      $.post('/store/'+me.options.parentView.options.store.get('name')+'/config/'+me.model.id+'/update-extensions/', {
          extensions: JSON.stringify(extensions)
        }, function(res) {
          if (!res.ok)
            alert(res.error);
          else {
            var config = me.options.parentView.collection.get(res.id);
            if (!config) {  // New config
              config = new StoreConfigModel(res);
              me.options.parentView.collection.add(config, {at: 0});
              me.options.parentView.render();
            }
            else {
            }
            me.$('.extensions-tab').hide();
          }
        }, 'json');
    },

    saveVMArgs: function() {
      this.model.set({vm_args: this.$('.store-sub-tab .vm_args').val()});

      var me = this;
      $.post('/store/'+me.options.parentView.options.store.get('name')+'/update-vm-args/' + me.model.id + '/', {vm_args: this.model.get('vm_args')}, function(res) {
        if (!res.ok)
          alert(res.error);
        else {
          var config = me.options.parentView.collection.get(res.id);
          if (!config) {  // New config
            config = new StoreConfigModel(res);
            me.options.parentView.collection.add(config, {at: 0});
            me.options.parentView.render();
          }
          else {
          }
          me.$('.vm_args-tab').hide();
        }
      }, 'json');
    },

    render: function() {
      $(this.el).html($.mustache(this.template, this.model.toJSON()));

      var columns = this.$('.columns');
      this.model.get('columns').each(function(obj) {
        columns.append(obj.view.render().el);
      });

      this.$('.add-new-column').empty().append(this.model.get('newColumn').view.render().el);

      var facets = this.$('.facets');
      this.model.get('facets').each(function(obj) {
        facets.append(obj.view.render().el);
      });

      this.$('.raw').val(this.model.get('schema'));

      this.$('.add-new-facet').empty().append(this.model.get('newFacet').view.render().el);

      // Reset extensions view.
      this.options.extensionsView = null;

      return this;
    }
  });

  window.StoreConfigView = Backbone.View.extend({
    template: $('#store-config-tmpl').html(),

    events: {
      'submit form': 'importConfig'
    },

    initialize: function() {
      _.bindAll(this, 'render', 'importConfig');
    },

    importConfig: function() {
      var me = this;
      if (!me.$('.config_file').val()) {
        alert("Please select a config file to import.");
        return false;
      }
    },

    render: function() {
      var me = this;
      if (!this.options.rendered) {
        $(this.el).html($.mustache(this.template, {store: me.options.store}));
        this.options.rendered = true;
      }
      
      var itemContainer = this.$('.item-container');

      this.collection.each(function(item) {
        if (!item.view) {
          item.set({'store': me.options.store});
          var view = new StoreConfigItemView({
            model: item
          });
          view.options.parentView = me;
        }
        itemContainer.append(item.view.render().el);
      });

      return this;
    }
  });

  window.FileView = Backbone.View.extend({
    template: $('#file-tmpl').html(),

    events: {
      'click .remove': 'removeMe',
      'mouseout': 'mouseOut',
      'mouseover': 'mouseOver'
    },

    initialize: function() {
      _.bindAll(this, 'removeMe', 'render', 'mouseOut', 'mouseOver');
      this.model.view = this;
    },

    removeMe: function() {
      this.options.parentView.collection.remove(this.model);
      $(this.el).detach();
    },

    mouseOut: function() {
      this.$('.op').hide();
    },

    mouseOver: function() {
      this.$('.op').show();
    },

    render: function() {
      $(this.el).html($.mustache(this.template, this.model.toJSON()));

      return this;
    }
  });

  window.FilesView = Backbone.View.extend({
    template: $('#files-tmpl').html(),

    events: {
    },

    initialize: function() {
      _.bindAll(this, 'render');
    },

    render: function() {
      var me = this;
      if (!this.options.rendered) {
        $(this.el).html($.mustache(this.template, {}));
        this.options.rendered = true;
      }
      
      var itemContainer = this.$('.files-container');

      this.collection.each(function(item) {
        if (!item.view) {
          var view = new FileView({
            model: item
          });
          view.options.parentView = me;
          itemContainer.append(item.view.render().el);
        }
      });

      return this;
    }
  });

  window.ContentStoreView = Backbone.View.extend({
    template: $('#content-store-tmpl').html(),

    className: 'content-store-item',

    events:{
      'click .deleteStore': 'deleteStore',
      'click .purgeStore': 'purgeStore',
      'click .regenerate-api-key': 'regenerateApiKey',
      'click .stopStore': 'stopStore',
      'click .manage': 'showManage',
      'click .collaborators': 'showCollaborators',
      'click .index-loader': 'showIndexLoader',
      'click .loadindex': 'loadIndex',
      'click .cluster': 'showCluster',
      'click .close-all-tabs': 'closeAllTabs',
      'click .restart': 'restart'
    },

    stopStore: function(){
      var me = this;
      var model = this.model;
      var really = confirm("This will stop your store '" + model.get('name')
        + "', do you really want to continue?");
      if (!really)
        return false;

      $.blockUI({ message: '<h1><img class="indicator" src="/static/images/indicator.gif" /> Stopping ' + me.model.get('name') + ' ...</h1>' });
      $.getJSON('/store/stop-store/'+model.get('name'),function(resp){
        if (resp.status_display)
          me.$('.status').text(resp.status_display);
        if (resp.status < 15) {
          me.$('.running-info').hide();
          me.$('.endpoint').hide();
        }

        $.unblockUI();

        if (!resp["ok"]){
          alert(resp["msg"]);
        }
      });
    },
    
    deleteStore: function(){
      var model = this.model;
      var really = confirm("This will delete your store '" + model.get('name')
        + "', do you really want to continue?");
      if (!really)
        return false;

      $.blockUI({ message: '<h1><img class="indicator" src="/static/images/indicator.gif" /> Deleting ' + model.get('name') + ' ...</h1>' });
      $.getJSON('/store/delete-store/'+model.get('name'), function(resp){
        if (resp["ok"]){
          sinView.collection.remove(model);
          $(model.view.el).remove();
        }
        else{
          alert(resp["msg"]);
        }  
        $.unblockUI();
      });
    },

    purgeStore: function(){
      var me = this;
      var model = this.model;
      var really = confirm("This will delete ALL documents from your store '" + model.get('name')
        + "', do you really want to continue?");
      if (!really)
        return false;

      $.blockUI({ message: '<h1><img class="indicator" src="/static/images/indicator.gif" /> Purging ' + model.get('name') + ' ...</h1>' });
      $.getJSON('/store/purge-store/'+model.get('name'), function(res){
        if (res["ok"]){
          me.$('.numdocs').text('0');
          if (res.status_display)
            me.$('.status').text(res.status_display);
          if (res.status == 15)
            me.$('.endpoint').show();
        }
        else{
          alert(res["msg"]);
        }  
        $.unblockUI();
      });
    },

    initialize: function() {
      _.bindAll(this, 'showManage', 'closeAllTabs', 'showCollaborators', 'showIndexLoader', 'loadIndex', 'showCluster', 'restart', 'render', 'stopStore', 'regenerateApiKey', 'deleteStore', 'purgeStore');
      this.model.view = this;
    },

    loadIndex: function() {
      var me = this;
      var uri = me.$('.uri').val();
      if (uri.length == 0) {
        alert('Please give a uri to load, hdfs://host:port/path for example');
        return;
      }

      $.blockUI({ message: '<h1><img class="indicator" src="/static/images/indicator.gif" /> Loading...</h1>' });
      $.post('/store/'+me.model.get('name') + '/load-index/', {uri: uri}, function(res) {
        if (res["ok"]) {
          me.closeAllTabs();
          alert('New index loaded.');
          $.getJSON('/store/'+me.model.get('name') + '/with-running-info/', function(res) {
            if (res.ok) {
              me.model.set(res);
              var running_info = me.model.get('running_info');
              if (running_info && running_info.numdocs >=0) {
                me.$('.numdocs').text(me.model.get('running_info').numdocs);
                me.$('.running-info').show();
              }
              else {
                me.$('.status').text("Error");
              }
            }
            else {
              alert(res.error);
            }
          });
        }
        else {
          alert(res["msg"]);
        }
        $.unblockUI();
      }, 'json');
    },

    regenerateApiKey: function() {
      var me = this;
      var really = confirm("After the new key is generated, you have to reconfig ALL your client to use the new key. Do you really want to continue?");
      if (!really)
        return false;

      $.getJSON('/store/regenerate-api-key/' + me.model.get('name'), function(resp) {
        if (resp["ok"]) {
          me.$('.api-key').text(resp.api_key);
        }
        else {
          alert(resp["msg"]);
        }
      });
    },

    restart: function() {
      var me = this;
      $.blockUI({ message: '<h1><img class="indicator" src="/static/images/indicator.gif" /> Restarting ' + me.model.get('name') + ' ...</h1>' });
      $.getJSON('/store/restart-store/'+this.model.get('name') + '/', function(res) {
        var running_info = res.running_info;
        if (running_info && running_info.numdocs >=0) {
          me.$('.numdocs').text(running_info.numdocs);
          me.$('.running-info').show();
        }
        if (res.status_display)
          me.$('.status').text(res.status_display);
        if (res.status == 15)
          me.$('.endpoint').show();

        $.unblockUI();

        if (!res.ok)
          alert(res.error);
      });
    },

    showManage: function() {
      var me = this;
      me.closeAllTabs();
      me.$('.manage-tab').show();

      if (!me.options.configView) {
        var configs = new StoreConfigCollection;
        configs.url = '/store/configs/' + me.model.get('name');
        var configView = me.options.configView = new StoreConfigView({
          collection: configs
        });
        configView.options.store = me.model;
        configs.fetch({
          success: function (obj, res) {
            me.$('.manage-tab').empty().append(configView.render().el);
          },
          error: function (obj, res) {
            alert('Unable to get configs from the server.');
          }
        });
      }
    },

    closeAllTabs: function() {
      this.$('.store-tab').hide(); },

    showCollaborators: function() {
      var me = this;
      me.closeAllTabs();
      me.$('.collab-tab').show();
      if (!me.options.collabView) {
        var collabs = new CollabCollection;
        collabs.url = '/store/collaborators/' + me.model.get('name');
        var collabView = me.options.collabView = new CollabView({
          collection: collabs
        });
        collabView.options.store = me.model;
        collabs.fetch({
          success: function (col, res) {
            me.$('.collab-tab').empty().append(collabView.render().el);
          },
          error: function (col, res) {
            alert('Unable to get collaborators from the server.');
          }
        });
      }
    },

    showIndexLoader: function() {
      var me = this;
      me.closeAllTabs();
      me.$('.index-loader-tab').show();
    },

    showCluster: function() {
      var me = this;
      me.closeAllTabs();
      me.$('.cluster-tab').show();
      $.getJSON('/store/'+me.model.get('name') + '/cluster-svg/', function(res) {
        if (res.ok) {
          me.$('.cluster-display').html(res.cluster);
        }
        else {
          alert(res.error);
        }
      });
    },

    render: function() {
      var me = this;
      var obj = this.model.toJSON();
      obj.sin_host = location.hostname;
      obj.sin_port = location.port;
      obj.is_running = obj.status == 15;
      obj.has_running_info = obj.running_info && obj.running_info.numdocs >= 0;

      obj.dateToLocaleString = function(text) {
        return function(text, render) {
          return new Date(parseInt(render(text))).toLocaleString();
        }
      };
      obj.dateToString = function(text) {
        return function(text, render) {
          return new Date(parseInt(render(text))).formatDate('MM-dd-yyyy hh:mm:ss');
        }
      };

      $(this.el).html($.mustache(this.template, obj));
      this.$('.timeago').each(function(index, timeago) {
        timeago = $(timeago);
        timeago.text($.timeago(timeago.text()));
      });

      if (obj.status >= 15) {
        $.getJSON('/store/'+me.model.get('name') + '/with-running-info/', function(res) {
          if (res.ok) {
            me.model.set(res);
            var running_info = me.model.get('running_info');
            if (running_info && running_info.numdocs >=0) {
              me.$('.numdocs').text(me.model.get('running_info').numdocs);
              me.$('.running-info').show();
              var broker = 'http://'+me.model.get('broker_host')+':'+me.model.get('broker_port');
              $.ajax({
                url: broker+'/sensei/admin/jmx/'+encodeURIComponent(broker),
                type: 'POST',
                contentType: 'text/json',
                data: JSON.stringify({
                        type: 'list'
                      }),
                dataType: 'json',
                success:  function(data) {
                            if (!(data && data.value))
                              return;
                            var jmx = data.value;
                            var db = jmx['com.senseidb'];
                            if (!db)
                              return;
                            for (var name in db) {
                              if ((''+name).indexOf('zoie-name=') == 0) {
                                var mb = db[name];
                                if (mb.op && mb.op.loadIndex) {
                                  me.$('.index-loader').show();
                                }
                                return;
                              }
                            }
                          }
              });
            }
            else {
              me.$('.status').text("Error");
            }
          }
          else {
            alert(res.error);
          }
        });
      }

      return this;
    }
  });

  var validNewStore = function(obj, nodes) {
    var res = {ok: true};
    if (obj && obj.name && obj.name.length > 0) {
      if (nodes < 1) {
        nodes = 1;
      }
      if (obj.replica > nodes) {
        res['ok'] = false;
        res['error'] = "You have only "+nodes+" nodes, cannot serve "+obj.replica+" replicas.";
      }
    }
    else {
      res['ok'] = false;
      res['error'] = "Name is required.";
    }
    return res;
  };

  window.SinView = Backbone.View.extend({
    template: $('#sin-tmpl').html(),

    events: {
      'click .show-create-new': 'showCreateNew',
      'click .new-store-add': 'addNewStore'
    },

    initialize: function() {
      _.bindAll(this, "render", 'showCreateNew', 'addNewStore');
//    this.collection.bind('add', function(){alert('change event')});
    },

    showCreateNew: function() {
      this.$('.new-store').toggle();
    },

    addNewStore: function() {
      var me = this;
      var obj = {
        name: $.trim($('.new-store-name').val()),
        replica: parseInt($.trim($('.new-store-replica').val())),
        partitions: parseInt($.trim($('.new-store-partitions').val())),
        desc: $('.new-store-desc').val()
      };
      var res = validNewStore(obj, this.options.nodes_count);
      if (!res.ok) {
        alert(res.error);
        return;
      }
      $.post('/store/new-store/'+obj.name+'/', obj, function(res) {
        if (res.ok) {
          var store = new ContentStoreModel(res);
          me.collection.add(store, {at: 0});
          me.$('.new-store').hide();
          me.render();
        }
        else {
          alert(res.error);
        }
      }, 'json');
    },

    render: function() {
      if (!this.options.rendered) {
        $(this.el).html($.mustache(this.template, {}));
        this.options.rendered = true;
      }
      
      var replica = 2;
      if (this.options.nodes_count <= 1) {
        replica = 1;
      }
      this.$('.new-store-replica').val(replica);

      var storesContainer = this.$('.stores-container');

      this.collection.each(function(store) {
        if (!store.view) {
          var view = new ContentStoreView({
            model: store
          });
        }
        storesContainer.append(store.view.render().el);
      });

      return this;
    }
  });

  var baseSync = Backbone.sync;

  Backbone.sync = function(method, model, success, error) {
    _.bind(baseSync, this);

    var resp;

    switch (method) {
      case "read":
        if (model.read)
          resp = model.read();
        else
          return baseSync(method, model, success, error);
        break;
      case "create":
        if (model.create)
          resp = model.create();
        else
          return baseSync(method, model, success, error);
        break;
      case "update":
        if (model.update)
          resp = model.update();
        else
          return baseSync(method, model, success, error);
        break;
      case "delete":
        if (model.del)
          resp = model.del();
        else
          return baseSync(method, model, success, error);
        break;
    }

    if (resp) {
      success(resp);
    } else {
      error("Record not found");
    }
  };

  var SinSpace = Backbone.Router.extend({
    routes: {
      'dashboard':        'dashboard', //#dashboard
      '.*':               'index',
    },

    initialize: function() {
      _.bindAll(this, 'dashboard', 'manage');
    },

    index: function() {
      //console.log('>>> index called');
      this.dashboard();
      this.navigate('dashboard');
    },

    dashboard: function() {
      $.getJSON('/cluster/1/nodes/count/', function(res) {
        window.stores = new ContentStoreCollection;
        window.sinView = new SinView({
          collection: stores,
          nodes_count: res.count
        });
        stores.fetch({
          success: function (col, res) {
            $('#main-area').empty().append(sinView.render().el);
          },
          error: function (col, res) {
          }
        });
      });
    },

    manage: function(id) {
    }
  });

  window.sinSpace = new SinSpace();
  Backbone.history.start();
});

function _void (){
  
}
