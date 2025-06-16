import plotly.graph_objects as go
import plotly as plt
from src import utils
from dash_utils import *
import os
import base64
import jinja2 
import io
from PIL import Image


def get_heatmap(path, keys_yaml):
    settings, experimental_factors, organisms, max_vals, options_pretty, annotated_dict = get_data(path, keys_yaml)

    heatmaps=[]

    for value in settings:
        options = [key.replace('_num', '') for key in settings[value] if key.endswith('_num')]
        sorter = experimental_factors[value] + [o for o in options if o not in experimental_factors[value]]

        df_empty = settings[value].dropna(axis=1, how='all')
        sorter = [x for x in sorter if x in df_empty.columns]
        df = [settings[value][f'{key}_num'] for key in sorter]   

        annotated = [annotated_dict[value][key] for key in sorter if key in annotated_dict[value]]
        option_text = []
        label_text = []
        for key in sorter:
            if key in annotated_dict[value] and key in experimental_factors[value]:
                label_vals = []
                for elem in annotated_dict[value][key]:
                    splitted = elem.split('<br>')
                    new_val = []
                    for val in splitted:
                        if len(val) > 20:
                            new_val.append(f'{val[:18]}...')
                        else:
                            new_val.append(val)
                    label_vals.append('<br>'.join(new_val))
                label_text.append(label_vals)
            else:
                label_text.append('')

        for option in sorter:
            if option in experimental_factors[value]:
                option_text.append(color("red", f'<b>{options_pretty[option]}</b>'))
            else:
                option_text.append(color("black", options_pretty[option]))
                
        plotly_colors = [x for x in px.colors.qualitative.G10 if x != "#DC3912"]

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
        
        table_header = ['<b>Experimental Factors</b>'] + [f'<b>{k}</b>' for k in condition_labels]
        table_values = [[f"<b>{x.replace('_', ' ').title()}</b>" for x in experimental_factors[value]]]

        table_height = {}
        max_value_len = 0
        for lab in condition_labels:
            cond_vals = []
            for fac in experimental_factors[value]:
                if fac not in table_height:
                    table_height[fac] = 0
                if fac in condition_labels[lab]:
                    table_height[fac] = max(table_height[fac], len(list(set([str(x) for x in condition_labels[lab][fac]]))))
                    cond_vals.append('<br>'.join(list(set(annotate(condition_labels[lab][fac])))))
                    max_value_len = max(max_value_len, max([len(x) for x in condition_labels[lab][fac]]))
                else:
                    cond_vals.append('')
            table_values.append(cond_vals)

        full_table_height = 25 * (len(list(table_height.keys()))+1) + 25 * ((sum([table_height[x] for x in table_height]) + 2))
        table_cell_with = max(my_cell_width, max_value_len*10)
        table_width = table_cell_with * len(table_header)
        table_layout = go.Layout(
            width=my_width + left_margin + right_margin,
            height=full_table_height,
            margin=dict(l=left_margin-my_cell_width, r=right_margin + (my_width+table_cell_with-table_width), t=20, b=20),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        table = go.Figure(
            data=[
                go.Table(
                    header=dict(
                        values=table_header,
                        align='left',
                        fill=dict(
                            color='rgba(0,0,0,0)'
                        ),
                        font_size=12,
                        line_color='darkslategray',
                        ), 

                    cells=dict(
                        values=table_values,
                        align='left',
                        font=dict(
                            color=['red'] + ['black']*len(condition_labels)
                        ),
                        fill=dict(color='rgba(0,0,0,0)'),
                        line_color='darkslategray',
                        ))], 
            layout=table_layout)

        heatmaps.append((fig.to_html(full_html=False, include_plotlyjs='cdn'), table.to_html(full_html=False, include_plotlyjs='cdn')))
        #heatmaps.append(fig)

    return heatmaps


def color(color, text):
    return f"<span style='color:{str(color)}'> {str(text)} </span>"

