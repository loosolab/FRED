from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import plotly.graph_objects as go
import plotly as plt
import pandas as pd
import argparse
import pathlib
from src import utils
import numpy as np
from dash_utils import get_data


parser = argparse.ArgumentParser('Metadata Heatmap')
parser.add_argument('-p', '--path', type=pathlib.Path, required=True, help='The path of the metadata file')

args = parser.parse_args()
input_file = utils.read_in_yaml(args.path)
key_yaml = utils.read_in_yaml('keys.yaml')

settings, experimental_factors, organisms, max_vals = get_data(input_file, key_yaml)


app = Dash()

# Requires Dash 2.17.0 or later
app.layout = [
    #dcc.Dropdown(list(settings.keys()), list(settings.keys())[0], id='dropdown-selection'),
    dcc.Tabs(id="tabs-example-graph", value=f'tab-{list(settings.keys())[0]}', children=[
        dcc.Tab(label=f'Setting {x}', value=f'tab-{x}') for x in settings
    ]),
    dcc.Checklist(['Remove Empty'],[], id='checklist-selection'),
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
    if len(empty) > 0:
        df_empty = settings[value].dropna(axis=1, how='all')
        print(df_empty)
        sorter = [x for x in sorter if x in df_empty.columns]
        
    df = [settings[value][f'{key}_num'] for key in sorter]   
    annotated = [settings[value][key] for key in sorter if key in settings[value]]
    
    option_text = []

    for option in sorter:
        if option in experimental_factors[value]:
            option_text.append(color("red", option))
        else:
            option_text.append(color("black", option))
    

    show_factors = '<br>'.join([f'\u00b7 {x.replace('_', ' ')}' for x in experimental_factors[value]])
    
    colors = [[0, 'white']]
    print('HIER', max_vals[value])
    for i in range(1, max_vals[value]+1):
        print(i, max_vals[value], 1/(max_vals[value]), i*1/(max_vals[value]))
        colors.append([i*1/(max_vals[value]), plt.colors.DEFAULT_PLOTLY_COLORS[i]])
        if i*1/(max_vals[value]) != 1:
            colors.append([((i*1)/(max_vals[value]))+0.001, 'white'])
    print('COLORS', colors)
    heatmap = [go.Heatmap(
                   z=df,
                   zmin=0,
                   zmax=max_vals[value],
                   x=[settings[value]['condition_index'],settings[value]['sample_index']],
                   y=sorter,
                   #showscale=False,
                   customdata=annotated,
                   #hovertemplate = "value: %{customdata}",
                   hoverongaps = False,
                   colorscale = colors,
                   ),
                   go.Scatter(
                       x=[None],
                       y=[None],
                       mode="markers",
                       name=f"<b>Experimental Factors</b><br>{show_factors}<br>",
                       showlegend=True,
                       marker=dict(size=10, color="red", symbol='square'),
                   )
                   ]
    
    condition_labels = {}
    for i in range(len(settings[value]['condition_name'])):
        if settings[value]['condition_index'][i] not in condition_labels:
            cond = settings[value]['condition_name'][i]
            splitted = utils.split_cond(cond)
            label_value = ''
            for elem in splitted:
                if isinstance(elem[1], dict):
                    label_value += f'\u00b7 {elem[0].replace('_', ' ')}: {", ".join([elem[1][k] for k in elem[1]])}<br>'
                elif isinstance(elem[1], list):
                    if len(elem[1]>3):
                        label_value += f'\u00b7 {elem[0].replace('_', ' ')}: {", ".join(elem[1][:3])}, ...<br>'
                    else:
                        label_value += f'\u00b7 {elem[0].replace('_', ' ')}: {", ".join(elem[1])}<br>'
                else:
                    label_value += f'\u00b7 {elem[0].replace('_', ' ')}: {elem[1]}<br>'
        condition_labels[settings[value]['condition_index'][i]]= label_value

    #data_input += [go.Scatter(x=[None], y=[None], mode="markers", name=f"{idx}:<br>{condition_labels[idx]}", showlegend=True, marker=dict(size=10, symbol='square')) for idx in sorted(list(set(settings[value]['condition_index'])))]
    data_input = heatmap
    fig = go.Figure(data=data_input)
    #fig.add_trace(go.Bar(x=[settings[value]['condition_index'],settings[value]['sample_index']], y=[50]*len(sorter), marker_line=dict(width=5, color=plt.colors.DEFAULT_PLOTLY_COLORS), marker_color='rgba(158,202,225,0.0)'))
    #for i in range(len(list(set(settings[value]['condition_index'])))):
    #    y_vals = [-10]
    #    x_vals = [settings[value]['index'][x] for x in range(len(settings[value]['index'])) if settings[value]['condition_index'][x] == list(set(settings[value]['condition_index']))[i]]
    #    fig.add_trace(go.Bar(x=[sum(x_vals)/len(x_vals)], y=y_vals, name=list(set(settings[value]['condition_index']))[i], width=[len(x_vals)-0.05], marker_line=dict(width=5, color=plt.colors.DEFAULT_PLOTLY_COLORS[i]), marker_color='rgba(158,202,225,0.0)')) #name=list(set(settings[value]['condition_index']))[i], width=1*(len([x for x in settings[value]['condition_index'] if x == list(set(settings[value]['condition_index']))[i]]))))
    #fig.update_layout(barmode='group', bargap=0.03)
    fig.update_layout(yaxis=dict(tickmode='array', ticktext=option_text, tickvals=sorter))
    #fig.update_layout(legend_title_text=f'Organism: {organisms[value]}')
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(side="top")
    fig.update_yaxes(tickson='boundaries')
    fig.update_layout(height=50*len(sorter))
    fig.update_layout(width=200*len(settings[value]['sample_index']))
    fig.update_layout(
        plot_bgcolor='white'
    )
    fig.update_xaxes(
        showline=True,
        gridcolor='lightgrey'
    )
    fig.update_yaxes(
        showline=True,
        gridcolor='lightgrey'
    )
    
    fig.update_layout(legend_valign='top')
    for i in range(len(sorter)):
        fig.add_hline(i, line_dash="dash", line_color='lightgrey',layer='below')
    return fig

def color(color, text):
    return f"<span style='color:{str(color)}'> {str(text)} </span>"

if __name__ == '__main__':

    app.run(debug=True)