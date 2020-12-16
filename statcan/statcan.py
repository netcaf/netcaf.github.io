import pandas as pd
import geopandas as gpd
import plotly.express as px
import json
import logging

logging.basicConfig(level = logging.INFO,format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

    def prune_map(self, mapdata, mapdata_key, dataframe, dataframe_key):
        
        index_list = []
        for index, row in mapdata.iterrows():
            mkey = row[mapdata_key]
            if mkey not in dataframe[dataframe_key].values.astype('str'):
                i = mapdata.loc[mapdata[mapdata_key] == mkey].index.to_list()
                assert(len(i) == 1)
                index_list += i
        pruned = mapdata.drop(index=index_list)
        
        print('Pruned: {} -> {}'.format(len(mapdata), len(pruned)))
        return pruned

    def generate_tip_data(self, dataframe):
        
        tip_data = {}
        color = None
        for col in dataframe.columns:
            if col in ['GEO_NAME', 'GEO_CODE', 'CSD_TYPE_NAME','Not a visible minority']:
                tip_data[col] = False
            elif col in ['Total']:
                tip_data[col] = ':,'
            elif col in ['Total Minority']:
                tip_data[col] = ':,'
                tip_data[col+' ratio'] = (':.2%',dataframe[col].astype(float)/dataframe['Total'])
            else:
                if 'Chinese' == col:
                    color = dataframe[col].astype(float)/dataframe['Total Minority']
                tip_data[col+' ratio'] = (':.2%',dataframe[col].astype(float)/dataframe['Total Minority'])

        return tip_data

    def show(self, threshold, filename='out.html'):
        
        logger.info("Read map data.")
        country_map = gpd.read_file(self.choroplethmap_file).to_crs("EPSG:4326")
        #with open("test.json") as f:
        #    country_map = json.load(f)

        logger.info("Read population data.")
        df = pd.read_csv(self.update_data_file)
        
        logger.info("Filter with threshold.")
        df = df.loc[df['Total Minority'] >= threshold]
        
        logger.info("Generate tip data.")
        tip_data = self.generate_tip_data(df)
        
        mapdata_key = 'CSDUID'
        dataframe_key = 'GEO_CODE'
        logger.info("Prune map data.")
        country_map = self.prune_map(country_map, mapdata_key, df, dataframe_key)

        logger.info("Generate figure with choropleth_mapbox.")
        fig = px.choropleth_mapbox(df, geojson=country_map, featureidkey="properties.{}".format(mapdata_key), locations=dataframe_key, color=tip_data['Chinese ratio'][1],
                                   color_continuous_scale="sunsetdark",
                                   #mapbox_style="carto-positron",
                                   mapbox_style="open-street-map",
                                   center = {"lat": 43.0, "lon": -79.0},
                                   zoom=8,
                                   opacity=0.5,
                                   hover_name='GEO_NAME',
                                   hover_data=tip_data,
                                   template='ggplot2',
                                   labels={'color': 'Chinese'},
                                  )
  
        logger.info("Update layout.")
        fig.update_layout(margin={"r":0,"t":30,"l":0,"b":0}, title={"text":'Minorities in Canada with the threshold {}'.format(threshold),})
        
        if filename:
            logger.info("Write html.")
            fig.write_html(filename, include_plotlyjs=True)
            print('Write to {}'.format(filename))

        logger.info("Show it.")
        fig.show()

        logger.info("Done.")
    
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
    parser.add_argument('-t','--threshold', help='Threshold for minority population...', type=int, default=1000)
    args = parser.parse_args()

    cd = CensusData()
    if args.update:
        cd.update_data()
    else:
        cd.show(threshold=args.threshold)
