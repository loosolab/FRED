from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import plotly.graph_objects as go
import plotly as plt
import pandas as pd
import argparse
import pathlib
from src import utils
from src.heatmap.dash_utils import *
import numpy as np
from src.heatmap.dash_utils import get_data
import os
import base64
import io
from PIL import Image

parser = argparse.ArgumentParser('Metadata Heatmap')
parser.add_argument('-p', '--path', type=pathlib.Path, required=True, help='The path of the metadata file')

args = parser.parse_args()
input_file = utils.read_in_yaml(args.path)
key_yaml = utils.read_in_yaml('keys.yaml')

settings, experimental_factors, organisms, max_vals, options_pretty, annotated_dict = get_data(input_file, key_yaml)


app = Dash()

# Requires Dash 2.17.0 or later
app.layout = [
    dcc.Tabs(id="tabs-example-graph", value=f'tab-{list(settings.keys())[0]}', 
             children=[dcc.Tab(label=f'Setting {x}', value=f'tab-{x}') for x in settings]),
                       dcc.Checklist(['Show Empty'],[], id='checklist-selection'),
                       dcc.Graph(id='graph-content')
                       ]

@callback(
    Output('graph-content', 'figure'),
    Input('tabs-example-graph', 'value'),
    Input('checklist-selection', 'value')
)
def update_graph(value, empty):
    value = value.replace('tab-','')
    options = [key.replace('_num', '') for key in settings[value] if key.endswith('_num')]
    sorter = experimental_factors[value] + [o for o in options if o not in experimental_factors[value]]

    if not empty:
        df_empty = settings[value].dropna(axis=1, how='all')
        sorter = [x for x in sorter if x in df_empty.columns]
    df = [settings[value][f'{key}_num'] for key in sorter]   

    annotated = [annotated_dict[value][key] for key in sorter if key in annotated_dict[value]]
    label_text = []
    for key in sorter:
        if key in annotated_dict[value] and key in experimental_factors[value]:
            label_text.append(annotated_dict[value][key])
        else:
            label_text.append('')

    option_text = []

    for option in sorter:
        if option in experimental_factors[value]:
            option_text.append(color("red", f'<b>{options_pretty[option]}</b>'))
        else:
            option_text.append(color("black", options_pretty[option]))

    plotly_colors = [x for x in px.colors.qualitative.G10 if x != "#DC3912"]
    print(plotly_colors)
    colors = [[0, 'white']]
    for i in range(1, max_vals[value]+1):
        colors.append([i*1/(max_vals[value]), plotly_colors[i-1]])
        if i*1/(max_vals[value]) != 1:
            colors.append([((i*1)/(max_vals[value]))+0.001, 'white'])

    heatmap = [go.Heatmap(
                z=df,
                zmin=0,
                zmax=max_vals[value],
                x=[settings[value]['condition_index'],settings[value]['sample_index']],
                y=sorter,
                showscale=False,
                customdata=annotated,
                text=label_text,
                texttemplate="%{text}",
                hovertemplate = "%{customdata}",
                hoverongaps = False,
                colorscale = colors,
                ),
            ]
        
    condition_labels = {}
    for i in range(len(settings[value]['condition_name'])):
        if settings[value]['condition_index'][i] not in condition_labels:
            cond = settings[value]['condition_name'][i]
            splitted = utils.split_cond(cond)
            cond_dict = {}
            for elem in splitted:
                if isinstance(elem[1], dict):
                    vals = [elem[1][k] for k in elem[1]]
                else:
                    vals =  [elem[1]]
                if elem[0] in cond_dict:
                    cond_dict[elem[0]] += vals
                else:
                    cond_dict[elem[0]] = vals
            condition_labels[settings[value]['condition_index'][i]]= cond_dict

    data_input = heatmap
        
    my_cell_width = 150
    top_margin = 100
    bottom_margin = 0
    left_margin = 200
    right_margin = 200
    my_height = 50*len(sorter)
    my_width = my_cell_width*len(settings[value]["sample_index"])

    organism_path = os.path.join(os.path.dirname(__file__), 'images', f'{organisms[value]}.png')
    images = None

    if os.path.isfile(organism_path):
        plotly_logo = base64.b64encode(open(organism_path, 'rb').read())
        imgdata = base64.b64decode(plotly_logo)
        im = Image.open(io.BytesIO(imgdata))
        im_width, im_height = im.size
        y_side = top_margin
        my_ysize=y_side/my_height
        x_side = y_side*im_width / im_height
        my_xsize = x_side/my_width

        left_margin = max(200, x_side)

        images = [dict(
            source='data:image/png;base64,{}'.format(plotly_logo.decode()),
            xref="paper", yref="paper",
            x=0, y=1,
            sizey=my_ysize, sizex=my_xsize,
            xanchor="right", yanchor="bottom"
        )]


    layout = go.Layout(
        images = images,
        height=my_height + top_margin + bottom_margin,
        width=my_width + left_margin + right_margin,
        margin=dict(l=left_margin, r=right_margin, t=top_margin, b=bottom_margin),
        autosize=False,
        title=dict(
            text=f'<b>Setting {value}</b>', 
            font=dict(size=15), 
            automargin=False,
            yref='container',
            x=(left_margin+(0.1*150))/(my_width+left_margin+right_margin),
            y=1,
            xanchor="left", yanchor="top",
            subtitle=dict(
                text=f'Organism: {organisms[value]}',
                font=dict(size=14, lineposition='under'),
                ),
            ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            side="top",
            showline=True,
            gridcolor="lightgrey",
            automargin=False
        ),
        yaxis=dict(
            tickmode="array",
            ticktext=option_text, 
            tickvals=sorter,
            autorange="reversed",
            tickson="boundaries",
            showline=True,
            gridcolor="lightgrey",
            automargin=False
        ),
        legend=dict(
            #title=f"Organism: {organisms[value]}",
            orientation="h",
            x=0, y=0
        )
    )   
    fig = go.Figure(data=data_input, layout=layout) 

    for i in range(len(sorter)):
        fig.add_hline(i, line_dash="dash", line_color='lightgrey',layer='below')
        fig.add_hline(i-0.5, line_width=0.5) 
    fig.add_hline(len(sorter)-0.5, line_width=0.5)     

    for i in range(len(settings[value]['sample_index'])+1):
        fig.add_vline(i-0.5, line_width=0.5)
    
    fig.add_hrect(y0=-0.5, y1=len(experimental_factors[value])-0.5, line=dict(color="red", width=5), layer='above')
        
    return fig

def color(color, text):
    return f"<span style='color:{str(color)}'> {str(text)} </span>"

if __name__ == '__main__':

    app.run(debug=True)