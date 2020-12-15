import pandas as pd
import geopandas as gpd
import plotly.express as px
import json

flist = ('98-401-X2016059_English_CSV_data.csv',  # Canada, provinces and territories
        '98-401-X2016066_English_CSV_data.csv', # Census subdivisions (CSD) - Ontario only
        )

flist = ('98-401-X2016055_English_CSV_data.csv',)
class CensusData:
    def __init__(self):
        
        self.data_frame = None;
        self.update_data_file = 'canada.csv'
        self.choroplethmap_file = 'lcsd000a16a_e.json'
        self.visible_name_mapping = {
            "Total - Visible minority for the population in private households - 25% sample data": "Total",
            "Total visible minority population": "Total Minority"
        }

    def load_data_from_file(self, file_name):
        
        self.data_frame = pd.read_csv(file_name, dtype='unicode')
        for col in self.data_frame.columns:
            if col[:3] == 'DIM':
                self.data_frame.rename(columns={col:'PROFILE_NAME'}, inplace=True)
            if col == 'Dim: Sex (3): Member ID: [1]: Total - Sex':
                self.data_frame.rename(columns={col:'TOTAL'}, inplace=True)
            if col == 'GEO_CODE (POR)':
                self.data_frame.rename(columns={col:'GEO_CODE'}, inplace=True)

    def read_visible_minority_population(self, geo_name=''):
        
        a = self.data_frame
        if geo_name:
            a = self.data_frame[self.data_frame['GEO_NAME'] == geo_name]

        b = a[a['PROFILE_NAME'] == 'Total - Visible minority for the population in private households - 25% sample data']

        return (self.data_frame.iloc[i: i+15] for i in b.index)

    def read_visible_minority_population1(self, geo_name=''):
        
        a = self.data_frame
        if geo_name:
            a = self.data_frame[self.data_frame['GEO_NAME'] == geo_name]

        b = a[a['PROFILE_NAME'] == 'Total - Visible minority for the population in private households - 25% sample data']
        n = b.index[0]
        
        return self.data_frame.loc[n:n+14,['PROFILE_NAME','TOTAL']].T


    def update_data(self):
        
        population_by_category = {}
        for f in flist:
            self.load_data_from_file(f)
            visibles = self.read_visible_minority_population()
            for visible in visibles:
                
                population_by_category.setdefault('GEO_NAME', []).append(visible.GEO_NAME.to_list()[0])
                population_by_category.setdefault('GEO_CODE', []).append(visible.GEO_CODE.to_list()[0])
                if 'CSD_TYPE_NAME' in visible.columns:
                    value = visible.CSD_TYPE_NAME.to_list()[0]
                else:
                    value = ''
                population_by_category.setdefault('CSD_TYPE_NAME', []).append(value)

                for index, row in visible.iterrows():
                    name = row.PROFILE_NAME
                    count = row.TOTAL
                    
                    if name in self.visible_name_mapping:
                        name = self.visible_name_mapping[name]
                    population_by_category.setdefault(name, []).append(count)

        n = pd.DataFrame(population_by_category)
        out_data = n.loc[n['Chinese'].str.replace('.','',1).str.isdigit()]

        '''
        out_data.insert(len(out_data.columns), 'Chinese Ratio', 0)
        out_data2 = out_data.copy()
        for index, row in out_data.iterrows():
            total_chinese = out_data.loc[index, 'Chinese']
            total_minority = out_data.loc[index, 'Total Minority']

            try:
                ratio = float(total_chinese) / float(total_minority)
                ratio = '{:.4}'.format(ratio)
            except ZeroDivisionError:
                ratio = 0

            out_data2.loc[index, 'Chinese Ratio'] = ratio
        '''
        out_data = out_data[out_data['Total Minority'].astype(float) != 0]
        out_data.to_csv(self.update_data_file, index=False)

    def show(self):

        
        country_map = gpd.read_file(self.choroplethmap_file).to_crs("EPSG:4326")
        #with open("test.json") as f:
        #    country_map = json.load(f)

        df = pd.read_csv(self.update_data_file)
        
        tip_data = {}
        color = None
        for col in df.columns:
            if col in ['GEO_NAME', 'GEO_CODE', 'CSD_TYPE_NAME','Not a visible minority']:
                tip_data[col] = False
            elif col in ['Total']:
                tip_data[col] = ':,'
            elif col in ['Total Minority']:
                tip_data[col] = ':,'
                tip_data[col+' ratio'] = (':.2%',df[col].astype(float)/df['Total'])
            else:
                if 'Chinese' == col:
                    color = df[col].astype(float)/df['Total Minority']
                tip_data[col+' ratio'] = (':.2%',df[col].astype(float)/df['Total Minority'])
        
        fig = px.choropleth_mapbox(df, geojson=country_map, featureidkey="properties.CSDUID", locations='GEO_CODE', color=color,
                                   color_continuous_scale="sunsetdark",
                                   mapbox_style="carto-positron",
                                   center = {"lat": 43.0, "lon": -79.0},
                                   zoom=8,
                                   opacity=0.5,
                                   hover_name='GEO_NAME',
                                   hover_data=tip_data,
                                   template='ggplot2',
                                   #labels={'color': 'Chinese'},
                                  )
  
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        fig.show()
        pass
    
    def show2(self):
        token = open(".mapbox_token").read() 
        with open("test.json") as f:
            country_map = json.load(f)

        df = pd.read_csv(self.update_data_file, dtype={"Chinese": str})
        import numpy as np
        import plotly.graph_objects as go

        tip_data = {}
        color = None
        for col in df.columns:
            if col in ['GEO_NAME', 'GEO_CODE', 'CSD_TYPE_NAME','Not a visible minority']:
                tip_data[col] = False
            elif col in ['Total']:
                tip_data[col] = ':,'
            elif col in ['Total Minority']:
                tip_data[col] = ':,'
                tip_data[col+' ratio'] = (':.2%',df[col].astype(float)/df['Total'])
            else:
                if 'Chinese' == col:
                    color = df[col].astype(float)/df['Total Minority']
                tip_data[col+' ratio'] = (':.2%',df[col].astype(float)/df['Total Minority'])


        c = go.Choroplethmapbox(geojson=country_map, locations=df.GEO_CODE, featureidkey="properties.CSDUID",
                                z=df.Chinese,
                                    colorscale="Viridis", 
                                    #hovertemplate='<b>%{z} </b> <br>%{properties.CMANAME}<br> Success rate: %{color:.2f} <extra>%{properties.CMANAME}</extra>',
                                    hovertemplate='y:%{y}',
                                    marker_line_width=0)

        fig = go.Figure(c)
        fig.update_layout(mapbox_style="light", mapbox_accesstoken=token,
                  mapbox_zoom=8, mapbox_center = {"lat": 43.0902, "lon": -79.7129}) 
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        fig.show()


if __name__ == '__main__':

    from argparse import ArgumentParser
    
    parser = ArgumentParser(description='Minorities in Canada')
    parser.add_argument('-u','--update', action="store_true", help='Update data...', default=False)
    args = parser.parse_args()

    cd = CensusData()
    if args.update:
        cd.update_data()
    else:
        cd.show()
