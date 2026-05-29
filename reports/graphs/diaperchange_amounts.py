# -*- coding: utf-8 -*-
from django.utils import timezone
from django.utils.translation import gettext as _

import plotly.offline as plotly
import plotly.graph_objs as go

from reports import utils
from core.units import DIAPER_UNIT_CHOICES, convert_diaper, get_default_unit


def diaperchange_amounts(instances):
    """
    Create a graph showing daily diaper change amounts over time.
    :param instances: a QuerySet of DiaperChange instances.
    :returns: a tuple of the graph's html and javascript.
    """
    default_unit = get_default_unit("diaper")

    totals = {}
    for instance in instances:
        time_local = timezone.localtime(instance.time)
        date = time_local.date()
        if date not in totals.keys():
            totals[date] = 0
        amount = instance.amount or 0
        if amount and instance.amount_unit and instance.amount_unit != default_unit:
            amount = convert_diaper(amount, instance.amount_unit, default_unit)
        totals[date] += amount

    amounts = [round(amount, 2) for amount in totals.values()]
    trace = go.Bar(
        name=_("Diaper change amount"),
        x=list(totals.keys()),
        y=amounts,
        hoverinfo="text",
        textposition="outside",
        text=amounts,
    )

    layout_args = utils.default_graph_layout_options()
    layout_args["title"] = "<b>" + _("Diaper Change Amounts") + "</b>"
    layout_args["xaxis"]["title"] = _("Date")
    layout_args["xaxis"]["rangeselector"] = utils.rangeselector_date()
    unit_label = dict(DIAPER_UNIT_CHOICES).get(default_unit, "")
    layout_args["yaxis"]["title"] = _("Change amount") + (
        f" ({unit_label})" if unit_label else ""
    )

    fig = go.Figure({"data": [trace], "layout": go.Layout(**layout_args)})
    output = plotly.plot(fig, output_type="div", include_plotlyjs=False)
    return utils.split_graph_output(output)
