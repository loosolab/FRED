import plotly.graph_objects as go
import fred.src.utils as utils
from src.heatmap.dash_utils import *
import plotly.express as px
import os
import base64
import io
from PIL import Image
import numpy


def get_heatmap(
    path,
    keys_yaml,
    show_setting_id=True,
    only_factors=False,
    mode="samples",
    labels="factors",
    background=False,
    sample_labels=False,
    condition_labels=False,
    transpose=False,
    drop_defaults=False,
):
    (
        settings,
        experimental_factors,
        organisms,
        max_vals,
        options_pretty,
        annotated_dict,
        max_annotation,
        conditions,
    ) = get_data(
        path, keys_yaml, mode=mode, drop_defaults=drop_defaults, transpose=transpose
    )

    techniques = list(utils.find_keys(path, "techniques"))
    setting_techniques = {}
    if len(techniques) > 0:
        techniques = techniques[0]
        for elem in techniques:
            try:
                sett_id = elem["setting"]
                try:
                    technique = elem["technique"]
                    setting_techniques[sett_id] = technique
                except KeyError:
                    pass
            except KeyError:
                pass

    heatmaps = []

    for value in settings:
        fig = None
        if len(settings[value]) > 0:

            options = [
                key.replace("_num", "")
                for key in settings[value]
                if key.endswith("_num")
            ]

            if only_factors:
                sorter = experimental_factors[value]
            else:
                sorter = experimental_factors[value] + [
                    o for o in options if o not in experimental_factors[value]
                ]
            df_empty = settings[value].dropna(axis=1, how="all")
            sorter = [x for x in sorter if x in df_empty.columns]
            val_sorter = [0]
            for elem in sorter:
                if elem in max_annotation[value]:
                    val_sorter.append(
                        max(
                            val_sorter[-1] + (50 if not transpose else 150),
                            val_sorter[-1] + (15 * max_annotation[value][elem]) + 20,
                        )
                    )
                else:
                    val_sorter.append(val_sorter[-1] + (50 if not transpose else 150))

            df = [settings[value][f"{key}_num"] for key in sorter]
            annotated = [
                annotated_dict[value][key]
                for key in sorter
                if key in annotated_dict[value]
            ]
            if transpose:
                annotated = numpy.transpose(annotated)
            option_text = []
            label_text = []
            for key in sorter:
                if labels == "all" or (
                    labels == "factors"
                    and key in annotated_dict[value]
                    and key in experimental_factors[value]
                ):
                    label_vals = []
                    for elem in annotated_dict[value][key]:
                        splitted = elem.split("<br>")
                        new_val = []
                        for val in splitted:
                            if len(val) > 20:
                                new_val.append(f"{val[:18]}...")
                            else:
                                new_val.append(val)
                        label_vals.append("<br>".join(new_val))
                    label_text.append(label_vals)
                else:
                    label_text.append([""] * len(annotated_dict[value][key]))

            for option in sorter:
                if option in experimental_factors[value]:
                    option_text.append(color("red", f"<b>{options_pretty[option]}</b>"))
                else:
                    option_text.append(color("black", options_pretty[option]))

            plotly_colors = []

            colors_scales = [
                px.colors.qualitative.G10,
                px.colors.qualitative.Plotly,
                px.colors.qualitative.D3,
                px.colors.qualitative.T10,
            ]

            i = 0
            while len(plotly_colors) < max_vals[value]:
                plotly_colors += [
                    x
                    for x in colors_scales[i % len(colors_scales)]
                    if x not in ["#DC3912", "#EF553B", "#D62728", "#F58518"]
                ]
                i += 1

            colors = [[0, "white"]]
            for i in range(1, max_vals[value] + 1):
                colors.append([i * 1 / (max_vals[value]), plotly_colors[i - 1]])
                if i * 1 / (max_vals[value]) != 1:
                    colors.append([((i * 1) / (max_vals[value])) + 0.001, "white"])

            if transpose:
                if mode == "samples":
                    if condition_labels:
                        if sample_labels:

                            y_value = [
                                settings[value]["condition_label"],
                                settings[value]["sample_label"],
                            ]
                        else:
                            y_value = [
                                settings[value]["condition_label"],
                                settings[value]["sample_index"],
                            ]
                    else:
                        if sample_labels:
                            y_value = [
                                settings[value]["condition_index"],
                                settings[value]["sample_label"],
                            ]
                        else:
                            y_value = [
                                settings[value]["condition_index"],
                                settings[value]["sample_index"],
                            ]
                else:
                    if condition_labels:
                        y_value = settings[value]["condition_label"]
                    else:
                        y_value = settings[value]["condition_index"]

                x_value = val_sorter
                label_text = numpy.transpose(label_text)
                df = numpy.transpose(df)
            else:
                if mode == "samples":
                    if condition_labels:
                        if sample_labels:
                            x_value = [
                                settings[value]["condition_label"],
                                settings[value]["sample_label"],
                            ]
                        else:
                            x_value = [
                                settings[value]["condition_label"],
                                settings[value]["sample_index"],
                            ]
                    else:
                        if sample_labels:
                            x_value = [
                                settings[value]["condition_index"],
                                settings[value]["sample_label"],
                            ]
                        else:
                            x_value = [
                                settings[value]["condition_index"],
                                settings[value]["sample_index"],
                            ]
                else:
                    if condition_labels:
                        x_value = settings[value]["condition_label"]
                    else:
                        x_value = settings[value]["condition_index"]
                y_value = val_sorter

            heatmap = [
                go.Heatmap(
                    z=df,
                    zmin=0,
                    zmax=max_vals[value],
                    x=x_value,
                    y=y_value,
                    showscale=False,
                    customdata=annotated,
                    text=label_text,
                    texttemplate="%{text}",
                    hovertemplate="%{customdata}",
                    hoverongaps=False,
                    colorscale=colors,
                ),
            ]

            data_input = heatmap

            if mode == "samples":
                if sample_labels:
                    sample_label_height = max(settings[value]["sample_label_height"])
                else:
                    sample_label_height = 1
            else:
                sample_label_height = 0

            if condition_labels:
                condition_label_height = max(settings[value]["condition_label_height"])
            else:
                condition_label_height = 1

            my_cell_width = 150
            # my_cell_height = max(50, (15*max_annotation[value])+20)
            if transpose:
                top_margin = 100
                bottom_margin = 20
                left_margin = (150 if condition_labels else 100) + (
                    150 if sample_labels else 100
                )
                right_margin = 20
                my_width = val_sorter[-1]
                my_height = 50 * (
                    len(settings[value]["sample_index"])
                    if mode == "samples"
                    else len(settings[value]["condition_index"])
                )
            else:
                top_margin = (
                    15 * sample_label_height + 15 * condition_label_height + 70
                )  # minimum 100
                bottom_margin = 20
                left_margin = 200
                right_margin = 20
                my_height = val_sorter[-1]  # my_cell_height*len(sorter)

                if mode == "samples":
                    my_width = my_cell_width * len(settings[value]["sample_index"])
                else:
                    my_width = my_cell_width * len(settings[value]["condition_index"])
            organism_path = os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "images",
                f"{organisms[value]}.png",
            )
            images = None

            if os.path.isfile(organism_path):
                plotly_logo = base64.b64encode(open(organism_path, "rb").read())
                imgdata = base64.b64decode(plotly_logo)
                im = Image.open(io.BytesIO(imgdata))
                im_width, im_height = im.size
                y_side = 100
                my_ysize = y_side / my_height
                x_side = y_side * im_width / im_height
                my_xsize = x_side / my_width

                left_margin = max(left_margin, x_side)

                images = [
                    dict(
                        source="data:image/png;base64,{}".format(plotly_logo.decode()),
                        xref="paper",
                        yref="paper",
                        x=0,
                        y=1,
                        sizey=my_ysize,
                        sizex=my_xsize,
                        xanchor="right",
                        yanchor="bottom",
                    )
                ]

            between = []
            technique_list = (
                setting_techniques[value] if value in setting_techniques else None
            )
            if technique_list is not None:
                technique_list = f' - {", ".join(technique_list)}'
            else:
                technique_list = ""
            for i in range(len(val_sorter) - 1):
                between.append((val_sorter[i + 1] + val_sorter[i]) / 2)
            layout = go.Layout(
                images=images,
                height=my_height + top_margin + bottom_margin,
                width=my_width + left_margin + right_margin,
                margin=dict(
                    l=left_margin, r=right_margin, t=top_margin, b=bottom_margin
                ),
                autosize=False,
                title=dict(
                    text=(
                        f"<b>Setting {value}{technique_list}</b>"
                        if show_setting_id
                        else ""
                    ),
                    font=dict(size=15),
                    automargin=False,
                    yref="container",
                    x=(left_margin + (0.1 * 150))
                    / (my_width + left_margin + right_margin),
                    y=1
                    - (30 / (my_height + top_margin + bottom_margin) * 100)
                    / (my_height + top_margin + bottom_margin),
                    xanchor="left",
                    yanchor="top",
                    subtitle=dict(
                        text=f"Organism: {organisms[value]}",
                        font=dict(size=14, lineposition="under"),
                    ),
                ),
                plot_bgcolor="rgb(255, 255, 255)" if background else "rgba(0,0,0,0)",
                paper_bgcolor="rgb(255, 255, 255)" if background else "rgba(0,0,0,0)",
                xaxis=(
                    dict(
                        side="top",
                        automargin=False,
                    )
                    if not transpose
                    else dict(
                        tickmode="array",
                        ticktext=option_text,
                        tickvals=between,
                        side="top",
                        automargin=False,
                    )
                ),
                yaxis=(
                    dict(
                        tickmode="array",
                        ticktext=option_text,
                        tickvals=between,
                        autorange="reversed",
                        automargin=False,
                    )
                    if not transpose
                    else dict(
                        automargin=False,
                        autorange="reversed",
                    )
                ),
            )

            fig = go.Figure(data=data_input, layout=layout)
            if transpose:
                for i in val_sorter:
                    fig.add_vline(i, line_width=0.5)

                for i in between:
                    fig.add_vline(
                        i, line_dash="dash", line_color="lightgrey", layer="below"
                    )

                if mode == "samples":
                    for i in range(len(settings[value]["sample_index"]) + 1):
                        fig.add_hline(i - 0.5, line_width=0.5)
                else:
                    for i in range(len(settings[value]["condition_index"]) + 1):
                        fig.add_hline(i - 0.5, line_width=0.5)

                fig.add_vrect(
                    x0=0,
                    x1=val_sorter[len(experimental_factors[value])],
                    line=dict(color="red", width=5),
                    layer="above",
                )

            else:
                for i in val_sorter:
                    fig.add_hline(i, line_width=0.5)

                for i in between:
                    fig.add_hline(
                        i, line_dash="dash", line_color="lightgrey", layer="below"
                    )

                if mode == "samples":
                    for i in range(len(settings[value]["sample_index"]) + 1):
                        fig.add_vline(i - 0.5, line_width=0.5)
                else:
                    for i in range(len(settings[value]["condition_index"]) + 1):
                        fig.add_vline(i - 0.5, line_width=0.5)

                fig.add_hrect(
                    y0=0,
                    y1=val_sorter[len(experimental_factors[value])],
                    line=dict(color="red", width=5),
                    layer="above",
                )

            fig.update_layout(
                modebar={"remove": ["zoom", "pan", "zoomIn", "zoomOut", "autoScale"]}
            )
            fig.layout.yaxis.fixedrange = True

        heatmaps.append(
            (
                value,
                fig,
                conditions[value] if len(list(conditions[value].keys())) > 0 else None,
            )
        )
    return heatmaps


def color(color, text):
    return f"<span style='color:{str(color)}'> {str(text)} </span>"
