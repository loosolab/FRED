import plotly.graph_objects as go
import plotly as plt
from src import utils
from dash_utils import get_data
import os
import base64
import jinja2 


def get_heatmap(path, keys_yaml):
    settings, experimental_factors, organisms, max_vals = get_data(path, keys_yaml)

    heatmaps=[]

    for value in settings:
        options = [key.replace('_num', '') for key in settings[value] if key.endswith('_num')]
        sorter = experimental_factors[value] + [o for o in options if o not in experimental_factors[value]]

        df_empty = settings[value].dropna(axis=1, how='all')
        sorter = [x for x in sorter if x in df_empty.columns]

        df = [settings[value][f'{key}_num'] for key in sorter]   
        annotated = [settings[value][key] for key in sorter if key in settings[value]]
        
        option_text = []

        for option in sorter:
            if option in experimental_factors[value]:
                option_text.append(color("red", option))
            else:
                option_text.append(color("black", option))
        

        #show_factors = '<br>'.join([f'\u00b7 {x.replace('_', ' ')}' for x in experimental_factors[value]])
        
        colors = [[0, 'white']]
        for i in range(1, max_vals[value]+1):
            print(i, max_vals[value], 1/(max_vals[value]), i*1/(max_vals[value]))
            colors.append([i*1/(max_vals[value]), plt.colors.DEFAULT_PLOTLY_COLORS[i]])
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
                    hovertemplate = "value: %{customdata}",
                    hoverongaps = False,
                    colorscale = colors,
                    ),
                    ]
        
        condition_labels = {}
        for i in range(len(settings[value]['condition_name'])):
            if settings[value]['condition_index'][i] not in condition_labels:
                cond = settings[value]['condition_name'][i]
                splitted = utils.split_cond(cond)
                label_value = ''
                for elem in splitted:
                    if isinstance(elem[1], dict):
                        label_value += f'\u00b7 {elem[0].replace("_", " ")}: {", ".join([elem[1][k] for k in elem[1]])}<br>'
                    elif isinstance(elem[1], list):
                        if len(elem[1]>3):
                            label_value += f'\u00b7 {elem[0].replace("_", " ")}: {", ".join(elem[1][:3])}, ...<br>'
                        else:
                            label_value += f'\u00b7 {elem[0].replace("_", " ")}: {", ".join(elem[1])}<br>'
                    else:
                        label_value += f'\u00b7 {elem[0].replace("_", " ")}: {elem[1]}<br>'
            condition_labels[settings[value]['condition_index'][i]]= label_value

        data_input = heatmap
        
        organism_path = os.path.join(os.path.dirname('__file__'), 'images', f'{organisms[value]}.png')
        images = None
        if os.path.isfile(organism_path):
            plotly_logo = base64.b64encode(open(organism_path, 'rb').read())
            images = [dict(
                source='data:image/png;base64,{}'.format(plotly_logo.decode()),
                xref="paper", yref="paper",
                x=0.1, y=-0.5,
                sizex=0.4, sizey=0.4,
                xanchor="center", yanchor="bottom"
        )]

        layout = go.Layout(
            images = images,
            height=50*len(sorter)+300,
            width=150*len(settings[value]["sample_index"])+50,
            margin=dict(l=20, r=20, t=20, b=300),
            plot_bgcolor="white",
            xaxis=dict(
                side="top",
                showline=True,
                gridcolor="lightgrey"
            ),
            yaxis=dict(
                tickmode="array",
                ticktext=option_text, 
                tickvals=sorter,
                autorange="reversed",
                #automargin="left+top",
                tickson="boundaries",
                showline=True,
                gridcolor="lightgrey"
            ),
            legend=dict(
                title=f"Organism: {organisms[value]}",
                #orientation="h",
                #x=0.2, y=1.2
            )
        )    
        fig = go.Figure(data=data_input, layout=layout)      
        for i in range(len(sorter)):
            fig.add_hline(i, line_dash="dash", line_color='lightgrey',layer='below')   
        
        heatmaps.append(fig.to_html(full_html=False, include_plotlyjs='cdn'))

    return heatmaps


def color(color, text):
    return f"<span style='color:{str(color)}'> {str(text)} </span>"

