/*
 * Copyright 2004, 2005 University of Oslo, Norway
 *
 * This file is part of Cerebrum.
 *
 * Cerebrum is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * Cerebrum is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Cerebrum; if not, write to the Free Software Foundation,
 * Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
 */

// Initialize yui-stuff.
YAHOO.namespace('cereweb');
YAHOO.widget.Logger.enableBrowserConsole();

// Shorthand
log = YAHOO.log;
YD = YAHOO.util.Dom;
YE = YAHOO.util.Event;
YC = YAHOO.util.Connect;
cereweb = YAHOO.cereweb;


/**
* Safari/WebKit doesn't support the hasOwnProperty method of Object.
*/
if( !Object.prototype.hasOwnProperty ) {
    Object.prototype.hasOwnProperty = function( property ) {
        try {
            var prototype = this.constructor.prototype;
            while( prototype ) {
                if( prototype[ property ] == this[ property ] ) {
                    return false;
                }
                prototype = prototype.prototype;
            }
        } catch( e ) {}
        return true;
    }
}

/**
* Cereweb events.
*/
cereweb.events = {
    pageChanged: new YAHOO.util.CustomEvent('pageChanged'),
    sessionError: new YAHOO.util.CustomEvent('sessionError')
};
/**
* Reusable AJAX callbacks.
*/
cereweb.callbacks = {
    /**
     * This snippet tries to extract the 'content' div.
     * Finally it calls this.update(result).
     */
    htmlSnippet: function(scope, cfn, cfa, failure) {
        // Name of function to call with the resulting html.
        this.scope = scope;
        this.scope.__htmlSnippet_cfn = cfn;
        this.argument = cfa;
        this.failure = failure;
    }
}

cereweb.callbacks.htmlSnippet.prototype = {
    success: function(o, args) {
        var open, close, offset; // Search indices to keep track of div nest level.
        var begin = '<div id="content">';

        var offset = o.responseText.search(begin) + begin.length; // We don't include the div tag.
        var rest = o.responseText.substring(offset);
        var skipped_char = "";
        var content = "";

        var i = 1;
        while (i > 0) {
            content += skipped_char;

            open = rest.search('<div');
            close = rest.search('</div>');

            if (open < close && open > -1) {
                i += 1;
                offset = open;
            } else {
                i -= 1;
                offset = close;
            }

            content += rest.substring(0, offset);

            skipped_char = rest.substring(offset, offset + 1);
            rest = rest.substring(offset + 1);
        }
        var cfn = this.__htmlSnippet_cfn;
        this[cfn](content, o.argument);
    }
}

/**
 * Set the cereweb.debug variable to true to enable the YUI logger widget.
 * Useful for IE debugging.  Firebug is better though.
 */
//cereweb.debug = false;
//cereweb.debug = true;
if(cereweb.debug) {
    YE.onContentReady("container", function(o) {
        var logger = cereweb.createDiv('logger');
        var myLogReader = new YAHOO.widget.LogReader(logger);
    });
};

cereweb.utils = {
    createDiv: function (id, parent) {
        if (YAHOO.lang.isUndefined(parent))
            parent = document.body;
        else if (YAHOO.lang.isString(parent))
            parent = YD.get(parent);
        var el = document.createElement('div');

        if (YAHOO.lang.isString(id))
            el.setAttribute('id', id);

        parent.appendChild(el);
        return el;
    },
    getParam: function (url, name) {
        name = name.replace(/[\[]/,"\\\[").replace(/[\]]/,"\\\]");
        var regexS = "[\\?&]"+name+"=([^&#]*)";
        var regex = new RegExp(regexS);
        var results = regex.exec(url);
        if(results == null)
            return "";
        else
            return results[1];
    }
}
cereweb.createDiv = cereweb.utils.createDiv; // Backwards compatibility.

(function () {
    var clickToToggle = function (el, def) {
        el.style.display = def;
        YE.on(el.parentNode, 'click', function () {
            el.style.display = el.style.display ? "" : "none";
        });
    };

    var addCloseButton = function (el) {
        var cb = document.createElement('img');
        cb.src = '/yui/container/assets/close12_1.gif';
        YD.addClass(cb, 'upperRight');
        el.appendChild(cb);
        return cb;
    };

    var Messages = function(el) {
        this.container = el;
        var children = el.childNodes;

        for (var i=0; i<children.length; i++) {
            var child = children[i];
            if (child.tagName && child.tagName.toUpperCase() === 'DIV')
                this.register(children[i]);
        }
    };

    Messages.prototype = {
        add: function (title, message, is_error) {
            var msg = document.createElement('div');
            var n = document.createElement('h3');
            this.container.appendChild(msg);

            msg.appendChild(n);
            if (is_error)
                YD.addClass(msg, 'error');
            n.innerHTML = title;

            n = document.createElement('div');
            YD.addClass(n, 'short');
            n.innerHTML = message;
            msg.appendChild(n);

            return this.register(msg);
        },
        remove: function (id) {
            var msg = YD.get(id);
            if (msg)
                this.container.removeChild(msg);
        },
        register: function (el) {
            var id = YD.generateId(el, 'msg_');

            var traceback = YD.getElementsByClassName('traceback', 'div', el);
            if (traceback.length > 0) {
                clickToToggle(traceback[0], "none");
            };

            var cb = addCloseButton(el);
            YE.on(cb, 'click', function() {
                this.remove(el.id);
            }, this, true);
            return id;
        }
    }

    YE.onContentReady('messages', function() {
        cereweb.msg = new Messages(this);
    });
})();

/**
 * Some basic event handling.  Currently it only handles click events on
 * links.  To register a link, use cereweb.action.add.
 */
cereweb.action = {
    /** This object is private and should not be accessed directly. */
    _events: {},
    /**
     * To register (overload) a link target, provide the name of the link
     * target and a function that should be called when a link with this
     * target is clicked.
     *
     * The callback function is called with two arguments:
     *   name: The name of the target that was clicked.
     *   args: An array of extra arguments.
     *   args[0]: The click event that triggered our event.
     *   args[1]: The arguments we parsed from the link.
     */
    add: function(name, func, obj) {
        var event = this._events[name] || new YAHOO.util.CustomEvent(name);
        event.subscribe(func, obj, true);
        this._events[name] = event;
    },
    fire: function(event, action) {
        var subaction = '*/' + action.name.split('/')[1];
        var preaction = action.name.split('/')[0] + '/*'
        var my_action = this._events[action.name] || this._events[subaction] || this._events[preaction];
        if (my_action)
            my_action.fire(event, action.args);
    },
    parse: function(url) {
        var url = unescape(url.replace(/http.*\/\/.*?\//,''))
        var anchor = url.split('#');
        if (anchor.length > 1)
            url = anchor[1];
        var target = url.split('?');
        var elms = (target[1] || '').split('&');
        var args = {};

        for (var i = 0; i < elms.length; i++) {
            var x = elms[i].split('=');
            args[x[0]] = x[1];
        }

        return {'name': target[0], 'args': args};
    },
    clicked: function(e) {
        var target = YE.getTarget(e);

        if (target.nodeName.toLowerCase() === 'a') {
            var action = this.parse(target.href);
            this.fire(e, action);
        }
    },
    clear: function() {
        this._events = {};
    }
}
YE.addListener('container', "click", cereweb.action.clicked,
    cereweb.action, true);
cereweb.events.sessionError.subscribe(cereweb.action.clear, cereweb.action, true);

/**
 * This object creates dialogues of divs with both the "box" and the "edit"
 * classes.  It also adds links to the actions div so that the box can be
 * shown.
 */
cereweb.editBox = {
    create: function(el, header, body) {
        var editBox = new YAHOO.widget.Dialog(el, {
            'width': '600px',
            'draggable': true,
            'visible': false,
            'fixedcenter': true,
            'postmethod': 'form' });
        if (header)
            editBox.setHeader(header);
        if (body)
            editBox.setBody(body);
        editBox.render();
        editBox.hide();
        return editBox;
    },
    /* boolean function used to recognize editBoxes */
    isEditBox: function(el) {
        return YD.hasClass(el, 'box') &&
               YD.hasClass(el, 'edit');
    },
    /* parses the DOM and runs add on all editBoxes it finds */
    init: function() {
        var els = YD.getElementsBy(
            this.isEditBox, 'div', 'content');
        if (els.length > 0)
            YD.batch(els, this.add, this, true);
    },
    /**
     * transforms the element to a YAHOO Dialog, and adds a link to the
     * actions div that, when clicked, shows the dialog
     */
    add: function(el) {
        var link = document.createElement('a');
        var actions = YD.get('actions');
        if (actions === null) {
            return;
        }

        var list = actions.getElementsByTagName('ul');
        if (list.length > 0) {
            list = list[0];
            var li = document.createElement('li');
            li.appendChild(link);
            list.appendChild(li);
        } else {
            actions.appendChild(link);
            actions.appendChild(document.createElement('br'));
        }

        if (!el.id)
            YD.generateId(el, 'editBox_');

        var id = el.id;
        var header = el.getElementsByTagName('h3')[0];
        link.href = "#" + el.id;
        link.innerHTML = header.innerHTML;

        el.removeChild(header);

        var editBox = this.create(el, header.innerHTML);
        el.style.display = "";

        cereweb.action.add(id, this.toggle, editBox);
        var cancel_links = YD.getElementsByClassName("cancel", null, el);
        if (cancel_links.length > 0)
            YE.addListener(cancel_links, 'click', editBox.hide, editBox, true);
    },
    /**
     * toggle the dialogues visibility.
     */
    toggle: function(name, args) {
        var event = args[0];
        YE.preventDefault(event);
        if (this.element.style.visibility !== "visible")
            this.show();
        else
            this.hide();
    }
}
YE.onContentReady('content', cereweb.editBox.init, cereweb.editBox, true);

cereweb.tooltip = {
    init: function() {
        var els = YD.getElementsByClassName('tt', null, 'container');
        for (var i=0; i<els.length; i++)
            els[i].setAttribute('title', els[i].nextSibling.innerHTML);
        this.tt = new YAHOO.widget.Tooltip('tt', {context:els});
    }
}

/**
 * Some text and links are only to be shown to users without javascript,
 * and some text and links should only be shown to users with it.
 */
cereweb.javascript = {
    init: function() {
        var nojs = YD.getElementsByClassName('nojs', null, 'container');
        var jsonly = YD.getElementsByClassName('jsonly', null, 'container');
        if (nojs.length > 0) { YD.setStyle(nojs, "display", "none"); }
        if (jsonly.length > 0) { YD.setStyle(jsonly, "display", ""); }
        cereweb.tooltip.init();
    }
}
YE.onContentReady('container', cereweb.javascript.init);

cereweb.tabs = new YAHOO.widget.TabView('tabview');
cereweb.tabs.DOMEventHandler = function(e) { /* do nothing */ };

(function() {
    var flatten = function(args) {
        var data = [];
        for (var el in args) {
            if (!args.hasOwnProperty(el))
                continue;

            data[data.length] = el + '=' + args[el];
        }
        return data.join('&');
    };

    var make_path_absolute = function(url) {
        if (url.slice(0,1) !== '/')
            url = '/' + url;
        return url;
    };

    var get_header = function(el) {
        var elements = el.getElementsByTagName('h3');
        for (var i = 0; i < elements.length; i++) {
            var el = elements[i];
            return el;
        }
    };

    var get_cancel_button = function(el) {
        var elements = el.getElementsByTagName('input');
        for (var i = 0; i < elements.length; i++) {
            var el = elements[i];
            if (el.type === 'submit' && el.value === 'Cancel')
                return el;
        }
    };

    var inline_edit = function(name, args) {
        var event = args[0];
        var args = args[1];
        YE.preventDefault(event);

        var url = make_path_absolute(YE.getTarget(event).pathname);
        var id = args.id || args.entity;

        // Get or create the neccessary divs and dialogues.
        var el = YD.get('edit_' + id);
        if (el) {
            var myBox = el.obj;
        } else {
            el = cereweb.createDiv('edit_' + id, 'content');
            var myBox = cereweb.editBox.create(el, 'head', 'body');
            el.obj = myBox;
        }

        myBox.update = function(r) {
            myBox.setBody(r);
            var header = get_header(myBox.element)
            header.parentNode.removeChild(header);
            myBox.setHeader(header);

            var cancelButton = get_cancel_button(myBox.element);
            YE.on(cancelButton, 'click', function(e) {
                YE.preventDefault(e);
                myBox.hide();
            });

            myBox.show();
        }

        var callback = new cereweb.callbacks.htmlSnippet(myBox, 'update');
        var cObj = YC.asyncRequest('POST',
            url, callback, flatten(args));

    }
    cereweb.action.add('*/edit', inline_edit);
})();

(function() {
    var handleYes = function() {
        this.hide();
        document.location = this.target.href.replace('/confirm', '');
    }

    var handleNo = function() {
        this.hide();
    }

    var confirmDialogue = new YAHOO.widget.SimpleDialog('confirm_dialog', {
        visible: false,
        width: '20em',
        close: false,
        fixedcenter: true,
        modal: true,
        draggable: false,
        icon: YAHOO.widget.SimpleDialog.ICON_WARN,
        buttons: [
            { text: 'Yes', handler: handleYes, isDefault: false },
            { text: 'No', handler: handleNo, isDefault: true }
        ]});
    confirmDialogue.setHeader("Alert!");
    confirmDialogue.setBody("Are you sure you want to do this?");

    var confirm = function(event, args) {
        var e = args[0];
        YE.preventDefault(e);
        confirmDialogue.render(document.body);
        confirmDialogue.show();
        confirmDialogue.target = YE.getTarget(e);
    }

    cereweb.action.add('confirm/*', confirm);
})();

(function() {
    var progress = new YAHOO.widget.Overlay('progress',
            { 'visible': false, 'zIndex': 10 });
    progress.setHeader('');
    progress.setBody('<img src="/img/smload.gif" alt="loading" />');

    cereweb.ajax = {
        rendered: false,
        begin: function() {
            if (!this.rendered) {
                var r = YD.getRegion('container');
                progress.render('container');
                var m = YD.getRegion(progress.body);
                var w = m.right - m.left;
                progress.cfg.setProperty('x', r.right - w - 1);
                progress.cfg.setProperty('y', r.top + 1);
            }
            progress.show();
        },
        done: function() {
            progress.hide();
        }
    }
})();

if(cereweb.debug) {
    log('bases are loaded');
}
