from collections import OrderedDict
import itertools
import matplotlib.pyplot as plt
from IPython import get_ipython
import base64

def _get_html(obj):
    """Get the HTML representation of an object"""
    # TODO: use displaypub to make this more general
    ip = get_ipython()
    rep = ip.display_formatter.formatters['text/html'](obj)

    if rep is not None:
        return rep
    elif hasattr(obj, '_repr_html_'):
        html_rep = obj._repr_html_()
        if html_rep is not None:
            return html_rep

    png_rep = ip.display_formatter.formatters['image/png'](obj)

    if png_rep is not None:
        if isinstance(obj, plt.Figure):
            plt.close(obj)  # keep from displaying twice
        output = ('<img src="data:image/png;'
                  'base64,{0}">'.format(base64.b64encode(png_rep)))
        return output
    else:
        return "<p> {0} </p>".format(str(obj))


class StaticInteract(object):
    """Static Interact Object"""

    template = """
    <script type="text/javascript">
      function interactUpdate(div){{
         var outputs = div.getElementsByTagName("div");
         var controls = div.getElementsByTagName("input");

         var value = "";
         for(i=0; i<controls.length; i++){{
           if((controls[i].type == "range") || controls[i].checked){{
             value = value + controls[i].getAttribute("name") + controls[i].value;
           }}
         }}

         for(i=0; i<outputs.length; i++){{
           var name = outputs[i].getAttribute("name");
           if(name == value){{
              outputs[i].style.display = 'block';
           }} else if (!name) {{
               outputs[i].style.display = 'block';
           }}else if(name != "controls"){{
              outputs[i].style.display = 'none';
           }}
         }}
      }}
    </script>

    <div>
      {outputs}
      {widgets}
    </div>
    """

    subdiv_template = """
    <div name="{name}" style="display:{display}">
      {content}
    </div>
    """

    @staticmethod
    def _get_strrep(val):
        """Need to match javascript string rep"""
        # TODO: is there a better way to do this?
        if isinstance(val, str):
            return val
        elif val % 1 == 0:
            return str(int(val))
        else:
            return str(val)

    def __init__(self, function, **kwargs):
        # TODO: implement *args (difficult because of the name thing)
        # update names
        for name in kwargs:
            kwargs[name] = kwargs[name].renamed(name)

        self.widgets = OrderedDict(kwargs)
        self.function = function

    def _output_html(self):
        names = [name for name in self.widgets]
        values = [widget.values() for widget in self.widgets.values()]
        defaults = tuple([widget.default for widget in self.widgets.values()])

        results = [self.function(**dict(zip(names, vals)))
                   for vals in itertools.product(*values)]

        divnames = [''.join(['{0}{1}'.format(n, self._get_strrep(v))
                             for n, v in zip(names, vals)])
                    for vals in itertools.product(*values)]

        display = [vals == defaults for vals in itertools.product(*values)]

        tmplt = self.subdiv_template
        return "".join(tmplt.format(name=divname,
                                    display="block" if disp else "none",
                                    content=_get_html(result))
                       for divname, result, disp in zip(divnames,
                                                        results,
                                                        display))

    def _widget_html(self):
        return "\n<br>\n".join([widget.html()
                                for name, widget in self.widgets.items()])

    def html(self):
        return self.template.format(outputs=self._output_html(),
                                    widgets=self._widget_html())

    def _repr_html_(self):
        return self.html()

class StaticBuildObject(object):
    """
    Make build objects, useful for presentations
    Extended by StaticBuildFigure and StaticBuildTable
    """
    template = """
    <style>
    *:focus {{
     outline:none;
    }}
    </style>
    <script type="text/javascript">
    function ProgressForward(div){{
    var control = div.getElementsByTagName("input")[0];
    var outputs = div.getElementsByTagName("div");
    control.value = parseInt(control.value) + 1;
    if (control.value >= outputs.length - 1) {{
        control.value = outputs.length - 2;
    }}
    for(i=0; i<outputs.length; i++){{
        var name = outputs[i].getAttribute("name");
        if(name == "name" + control.value){{
            outputs[i].style.display = 'block';
        }} else if (name != "control"){{
            outputs[i].style.display = 'none'
        }}
    }}
    }}

    function ProgressBackward(div){{
    var control = div.getElementsByTagName("input")[0];
    var outputs = div.getElementsByTagName("div");
    control.value = parseInt(control.value) - 1;
    if (control.value <= 0) {{
        control.value=0;
    }}
    for(i=0; i<outputs.length; i++){{
        var name = outputs[i].getAttribute("name");
        if(name == "name" + control.value){{
            outputs[i].style.display = 'block';
        }} else if (name != "control"){{
            outputs[i].style.display = 'none'
        }}
    }}
    }}

    // Use "a" to go forward, "r" to go back. Or click to progress
    function HandleKey(div){{
    var key = window.event.keyCode;
    if (key == 65) {{
       ProgressForward(div);
    }}
    if (key == 82) {{
       ProgressBackward(div);
    }}
    }}
    </script>
    <div name="control" {clicktype}="ProgressForward(this.parentNode);return false;" onkeyup="HandleKey(this.parentNode);" tabindex="0">
      {outputs}
      <input type="none" value="0" style="display:none;">
    </div>
    """

    subdiv_template = """
    <div name="{name}" style="display:{display}">
      {content}
    </div>
    """
    def __init__(self, function_list, apply_to_all=None, center=False, rightclick=False):
        self.function_list = function_list
        self.apply_to_all = apply_to_all
        self.center = center
        self.rightclick = rightclick

    def GenerateStaticFrames(self):
        """ overridden by children classes """
        return None

    def _output_html(self):
        # get results
        results = []
        for i in range(len(self.function_list)+1):
            results.append(self.GenerateStaticFrames(i))

        # Get divnames (name<i> is after applying first i functions)
        divnames = ['name%s'%i for i in range(len(self.function_list)+1)]

        display = [True] + [False]*(len(self.function_list))

        tmplt = self.subdiv_template
        return "".join(tmplt.format(name=divname,
                                    display="block" if disp else "none",
                                    content=_get_html(result))
                       for divname, result, disp in zip(divnames,
                                                        results,
                                                        display))

    def _get_clicktype(self):
        if self.rightclick: return "oncontextmenu"
        else: return "onclick"

    def html(self):
        return self.template.format(outputs=self._output_html(), clicktype=self._get_clicktype())

    def _repr_html_(self):
        if self.center:
            return "<center>{0}</center>".format(self.html())
        return self.html()

class StaticBuildTable(StaticBuildObject):
    """
    Make build tables, useful for presentations
    """

    def __init__(self, pretty_table, function_list, center=False, rightclick=False):
        self.function_list = function_list
        self.pretty_table = pretty_table
        self.center = center
        self.rightclick = rightclick

    def GenerateStaticFrames(self, i):
        pt = self.pretty_table.copy()
        for f in self.function_list[0:i]:
            f(pt)
        return pt

class StaticBuildFigure(StaticBuildObject):
    """
    Make build figures, useful for presentations.

    StaticBuildFigure(function_list, apply_to_all=None)
    function_list: list of functions. Each function must take in
      a pyplot.Axes instance and modify that axis
    apply_to_all: apply this function to all plots
    center: center the output html
    rightclick: change the figure on right click instead of click

    Generate "build" figures, progressively applying functions in
      the list. Each time you right click on the figure, apply the next
      function. Press "a" (advance) or "r" (reverse) to
      move forward and backward through the animation

    Example:
    def f1(ax):
      ax.axhline(y=2)

    def f2(ax):
      ax.axhline(y=3)

    def init(ax):
      ax.set_xlabel("This is the X axis")
      ax.set_ylabel("This is the Y axis")
      ax.set_xlim(left=0, right=1)
      ax.set_ylim(bottom=0, top=5)

    StaticBuildFigure([f1, f2], apply_to_all=init)
    """

    def GenerateStaticFrames(self, i):
        """
        Generate figure after applying the first i functions
        """
        fig = plt.figure()
        ax = fig.add_subplot(111)
        for f in self.function_list[0:i]:
            f(ax)
        if self.apply_to_all is not None: self.apply_to_all(ax)
        return fig

class StaticBuildHtml(StaticBuildObject):
    """
    Make build htmls, useful for presentations.

    StaticBuildHtml([html1, html2,..])
    """

    def GenerateStaticFrames(self, i):
        """
        Generate figure after applying the first i functions
        """
        if i < len(self.function_list):
            return self.function_list[i]
        else:
            return self.function_list[-1]

