import pandas as pd
import geopandas as gpd
import plotly.express as px
import numpy as np
import json
import logging
import math

logging.basicConfig(level = logging.INFO,format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CensusData:
    def __init__(self, year, threshold):
        
        self.year = year
        self.threshold = threshold
        self.data_frame = None
        self.update_data_file = 'tmp.canada.csv'
        #self.update_map_file = 'canada.json'
        #self.choroplethmap_file = 'lcsd000a16a_e.json'
        self.visible_name_mapping = {
            "Total - Visible minority for the population in private households - 25% sample data": "Total",
            "Total visible minority population": "Total Minority"
        }

        if self.year == 2016:
            self.flist = (
                '98-401-X2016059_English_CSV_data.csv',  # Canada, provinces and territories
                '98-401-X2016066_English_CSV_data.csv', # Census subdivisions (CSD) - Ontario only
            )

            self.choroplethmap_file = 'lcsd000a16a_e.json'
        else:
            self.flist = (
                '98-401-X2021001_English_CSV_data.csv',
                '98-401-X2021005_eng_CSV/98-401-X2021005_English_CSV_data.csv'
            )
            self.choroplethmap_file = 'lcsd000a21a_e.json'

        print(self.year)
        print(self.choroplethmap_file)
        print(self.flist)

    def load_data_from_file(self, file_name):
        
        #self.data_frame = pd.read_csv(file_name, encoding = "utf-8", dtype='unicode')
        self.data_frame = pd.read_csv(file_name, encoding = "ISO-8859-1")
        for col in self.data_frame.columns:

            if col[:3] == 'DIM' or col == 'CHARACTERISTIC_NAME':
                self.data_frame.rename(columns={col:'PROFILE_NAME'}, inplace=True)
            
            if col == 'Dim: Sex (3): Member ID: [1]: Total - Sex' or col == 'C1_COUNT_TOTAL':
                self.data_frame.rename(columns={col:'TOTAL'}, inplace=True)

            #if col == 'GEO_CODE (POR)' or col == 'ALT_GEO_CODE':
            if col == 'ALT_GEO_CODE':
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
        for f in self.flist:
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
                    
                    name = name.strip()
                    if name in self.visible_name_mapping:
                        name = self.visible_name_mapping[name]
                    #name = name.strip()
                    population_by_category.setdefault(name, []).append(count)

        n = pd.DataFrame(population_by_category)
        out_data = n.loc[n['Chinese'].astype(str).str.replace('.','',1,regex=False).str.isdigit()]

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

    def generate_tip_data1(self, dataframe):
        
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

    def load_data(self, update=False, mapdata_key='CSDUID', dataframe_key='GEO_CODE'):
        
        d_file = 'canada.filtered.csv'
        m_file = 'map.pruned.json'
        
        if update:
            logger.info("Read map data.")
            country_map = gpd.read_file(self.choroplethmap_file).to_crs("EPSG:4326")
            
            logger.info("Read population data.")
            df = pd.read_csv(self.update_data_file)
        
            logger.info("Filter with threshold.")
            df = df.loc[df['Total Minority'] >= self.threshold]
            
            logger.info("Prune map data.")
            country_map = self.prune_map(country_map, mapdata_key, df, dataframe_key)

            df.to_csv(d_file, index=False)
            country_map.to_file(m_file, driver='GeoJSON')
        else:
            
            logger.info("Read map data.")
            country_map = gpd.read_file(m_file).to_crs("EPSG:4326")
            
            logger.info("Read population data.")
            df = pd.read_csv(d_file)

        return (df, country_map)

    def show(self, filename='out.html'):
        
        mapdata_key = 'CSDUID'
        dataframe_key = 'GEO_CODE'

        df, country_map = self.load_data(update=True, mapdata_key=mapdata_key, dataframe_key=dataframe_key)

        logger.info("Generate tip data.")
        tip_data = self.generate_tip_data(df)
        
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
                                   #labels={'color': 'Chinese ratio1'},
                                  )
  
        logger.info("Update layout.")
        fig.update_layout(margin={"r":0,"t":30,"l":0,"b":0}, title={"text":'Minorities in Canada (Total Minority >= {})'.format(self.threshold),})
        fig.update_layout(
            hoverlabel_align = 'right',
            hoverlabel=dict(
                bgcolor="aliceblue",
                font_size=16,
                font_family="Rockwell"
            )
        )
        
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


def shp_to_geojson():
    myshpfile = gpd.read_file('lcsd000a16a_e/lcsd000a16a_e.shp')
    myshpfile_out = myshpfile.to_crs('EPSG:4326')
    myshpfile_out.to_file('lcsd000a16a_e.json', driver='GeoJSON')
    
if __name__ == '__main__':

    from argparse import ArgumentParser
    
    parser = ArgumentParser(description='Minorities in Canada')
    parser.add_argument('-u','--update', action="store_true", help='Update data...', default=False)
    parser.add_argument('-t','--threshold', help='Threshold for minority population...', type=int, default=1000)
    parser.add_argument('-y','--year', type=int, choices=[2016, 2021], default=2016, help='Census year...')
    args = parser.parse_args()

    cd = CensusData(args.year, args.threshold)
    if args.update:
        cd.update_data()
    else:
        cd.show(filename='canada.{}.{}.html'.format(args.year, args.threshold))
