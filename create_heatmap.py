import plotly.graph_objects as go
import plotly as plt
from src import utils
from dash_utils import get_data

def get_heatmap(path, keys_yaml):
    settings, experimental_factors, organisms, max_vals = get_data(path, keys_yaml)

    heatmaps=[]

    for value in settings:
        options = [key.replace('_num', '') for key in settings[value] if key.endswith('_num')]
        sorter = experimental_factors[value] + [o for o in options if o not in experimental_factors[value]]
            
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
                    zmax=3,
                    x=[settings[value]['condition_index'],settings[value]['sample_index']],
                    y=sorter,
                    #showscale=False,
                    customdata=annotated,
                    #hovertemplate = "value: %{customdata}",
                    hoverongaps = False,
                    colorscale = colors,
                    )]
        
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
        fig = go.Figure(data=data_input)
        fig.update_coloraxes(cmin=1, cmax= 3)
       
        fig.update_layout(yaxis=dict(tickmode='array', ticktext=option_text, tickvals=sorter))
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
        heatmaps.append(fig.to_html(full_html=False, include_plotlyjs='cdn'))
    return heatmaps


def color(color, text):
    return f"<span style='color:{str(color)}'> {str(text)} </span>"

