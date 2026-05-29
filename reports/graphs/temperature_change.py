# -*- coding: utf-8 -*-
from django.utils.translation import gettext as _

import plotly.offline as plotly
import plotly.graph_objs as go

from reports import utils
from core.units import TEMP_UNIT_CHOICES, convert_temperature, get_default_unit


def temperature_change(objects):
    """
    Create a graph showing temperature over time.
    :param objects: a QuerySet of Temperature instances.
    :returns: a tuple of the graph's html and javascript.
    """
    objects = objects.order_by("-time")
    default_unit = get_default_unit("temperature")

    times = list(objects.values_list("time", flat=True))
    temperatures = [
        convert_temperature(o.temperature, o.temperature_unit, default_unit)
        if o.temperature_unit and o.temperature_unit != default_unit
        else o.temperature
        for o in objects
    ]

    trace = go.Scatter(
        name=_("Temperature"),
        x=times,
        y=temperatures,
    )

    layout_args = utils.default_graph_layout_options()
    layout_args["barmode"] = "stack"
    layout_args["title"] = "<b>" + _("Temperature") + "</b>"
    layout_args["xaxis"]["title"] = _("Time")
    layout_args["xaxis"]["type"] = "date"
    layout_args["xaxis"]["autorange"] = True
    layout_args["xaxis"]["autorangeoptions"] = utils.autorangeoptions(trace.x)
    layout_args["xaxis"]["rangeselector"] = utils.rangeselector_time()
    unit_label = dict(TEMP_UNIT_CHOICES).get(default_unit, "")
    layout_args["yaxis"]["title"] = _("Temperature") + (
        f" ({unit_label})" if unit_label else ""
    )

    fig = go.Figure({"data": [trace], "layout": go.Layout(**layout_args)})
    output = plotly.plot(fig, output_type="div", include_plotlyjs=False)
    return utils.split_graph_output(output)
