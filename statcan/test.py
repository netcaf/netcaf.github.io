import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class CensusData:
    def __init__(self, filename='98-401-X2016059_English_CSV_data.csv'):
        self.df = pd.read_csv(filename)
        for col in self.df.columns:
            if col[:3] == 'DIM':
                self.df.rename(columns={col:'DIM'}, inplace=True)
            if col == 'Dim: Sex (3): Member ID: [1]: Total - Sex':
                self.df.rename(columns={col:'TotalSex'}, inplace=True)

    def read_visible_minority_population(self, geo_value='Canada'):
        d = {
            "Total - Visible minority for the population in private households - 25% sample data":"",
            "Total visible minority population":"",
            "South Asian":"",
            "Chinese":"",
            "Black":"",
            "Filipino":"",
            "Latin American":"",
            "Arab":"",
            "Southeast Asian":"",
            "West Asian":"",
            "Korean":"",
            "Japanese":"",
            "Visible minority, n.i.e.":"",
            "Multiple visible minorities":"",
            "Not a visible minority":"",
        }
        a = self.df[self.df['GEO_NAME']==geo_value]
        b = a[a['DIM'] == 'Total - Visible minority for the population in private households - 25% sample data']
        i = b.index[0]
        
        return self.df.iloc[i: i+15]

class SubCensusOntario(CensusData):
    def __init__(self, filename='98-401-X2016066_English_CSV_data.csv'):
        super().__init__(filename)

def show_fig(d):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    
    n = len(d)
    specs=[[{'type':'domain'}]]*n
    fig = make_subplots(rows=n, cols=1, specs=specs) 
    for index, key in enumerate(d, start=1):
        values = d[key]['TotalSex'][2:]
        labels = d[key]['DIM'][2:]
        
        pull = []
        for l in labels:
            if l == 'Chinese':
                pull += [0.5]
            else:
                pull += [0]
        fig.add_trace(go.Pie(values = values, labels=labels, title={'text':key, 'position':'middle center','font': dict(family="Courier New, monospace", size=18, color="Red")}, pull=pull, showlegend=True, hole=0.3, opacity=0.9), index,1)
    
    fig.update_layout(autosize=False, width=1500, height=1500*n,)
    fig.show()

def show_fig_burst(d, name=''):
    n = len(d)
    specs=[[{'type':'domain'}]]*n
    fig = make_subplots(rows=n, cols=1, specs=specs) 

    for index, key in enumerate(d, start=1):
        data = d[key]
        ids = data['DIM'].to_list()
        ids[0] = key
        parents = [ids[1]]*len(ids)
        parents[0] = ''
        parents[1] = ids[0]
        parents[-1] = ids[0]
        
        fig.add_trace(go.Sunburst(labels=ids, parents=parents, values=data['TotalSex'], branchvalues='total'), index,1)

    fig.update_layout(autosize=False, width=1200, height=800*n,)
    fig.show()

def GetData():
    data_list = ['Canada', 
                'Newfoundland and Labrador',
                'Prince Edward Island', 
                'Nova Scotia', 
                'New Brunswick', 
                'Quebec', 
                'Ontario', 
                'Manitoba', 
                'Saskatchewan', 
                'Alberta', 
                'British Columbia', 
                'Yukon', 
                'Northwest Territories', 
                'Nunavut']
    cd = CensusData()
    canada_data = {}
    for d in data_list:
        canada_data[d] = cd.read_visible_minority_population(d)
    
    #show_fig(canada_data)

    data_list = ["Ottawa","Toronto","Ajax",
                "Clarington",
                "Brock",
                "Oshawa",
                "Pickering",
                "Scugog",
                "Uxbridge",
                "Whitby",
                "Burlington",
                "Halton Hills",
                "Milton",
                "Oakville",
                "Brampton",
                "Caledon",
                "Mississauga",
                "Aurora",
                "East Gwillimbury",
                "Georgina",
                "King",
                "Markham",
                "Newmarket",
                "Richmond Hill",
                "Vaughan",
                "Whitchurch-Stouffville",
                "Hamilton",
                "Kitchener",
                "London",
                "Cambridge",
                "Waterloo"]
    
    cd = SubCensusOntario()
    ontario_data = {}
    for d in data_list:
        data = cd.read_visible_minority_population(d)
        ontario_data['Ontario - ' + d] = data


    canada_data.update(ontario_data)
    show_fig(canada_data)

GetData()
