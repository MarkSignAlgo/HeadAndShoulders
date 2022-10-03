import requests
import pandas as pd
import json


def rhns(df, length, holding, loss_cut):
    positions=list()
    i=0
    while i<(len(df)-length-holding-1):
        try:
            dfi=df[i:i+length]
            #breaking down the interval in 3 parts
            v=int(length/3)
            fdfi=dfi[:v]
            sdfi=dfi[v:2*v]
            ldfi=dfi[2*v:]
            #getting the local minimums for each part
            m1=fdfi['close'].max()
            m2=sdfi['close'].max()
            m3=ldfi['close'].max()
            im1=fdfi.index[fdfi['close']==m1].values.tolist() #it's a list. If more than 1 value BREAK
            im2=sdfi.index[sdfi['close']==m2].values.tolist()
            im3=ldfi.index[ldfi['close']==m3].values.tolist()
            if len(im1)>1 or len(im2)>1 or len(im3)>1:
                i=i+1
                continue
            locfdfi=dfi.loc[im1[0]:im2[0]]
            locsdfi=dfi.loc[im2[0]+1:im3[0]]
            lm1=locfdfi['close'].min()
            lm2=locsdfi['close'].min()
            #making sure there is enough "space" between the maximums
            if im3[0]-im1[0]<int(v/2):
                ldfii=dfi[(2*v+int(v/2)):]
                ldfia=dfi[2*v:(2*v+int(v/2))]
                m3=ldfii['close'].max()
                lm2=ldfia['close'].min()
                if lm2>m3:
                    i=i+1
                    continue
            if m2>m1 and m2>m3:
                #making sure the shoulders are at a similar level (??) >> tHIS COULD BE REMOVED
                if m1>0.98*m3 and m1<1.02*m3:
                    #making sure the local minimums are a certain level below the relevant maximums (??) THIS TOO COULD BE REMOVED??
                    if lm1<m1 and lm2<m3:
                        #Reverse Head and shoulders identified
                        if df['close'].iloc[i+length+1]<dfi['close'].min():
                            #INITIATING SELL if next value is below the min of the interval
                            perf=df['close'].iloc[i+length+1+holding]/df['close'].iloc[i+length+1]-1
                            positions.append([i, i+length, perf, holding])
                            i=i+length+holding+1
                        else:
                            i=i+1
                    else:
                        i=i+1
                else:
                    i=i+1
            else:
                i=i+1
        except:
            full_rez={'positions':positions, 'message':'Error at step {}'.format(i)}
            return full_rez
    full_rez={'positions':positions,'message':'', 'vars':[length, holding]}
    return full_rez

def api_iex(stock):
    """
    function calls the IEX API and returns a pandas df of it.
    Make sure it starts with oldest date
    """
    link='https://cloud.iexapis.com/stable/stock/{}/chart/max?token=YOUR_TOKEN_HERE'.format(stock.lower())
    data=requests.get(link)
    try:
        dataj=data.json()
    except:
        return 'Error in get_data_api for {}.'.format(stock)
    data_list=list()
    for i in dataj:
        data_list.append([i['date'], i['open'], i['close'], i['low'], i['high'], i['volume']])
    df=pd.DataFrame(data_list, columns=['date', 'open', 'close', 'low', 'high', 'volume'])
    return df

def rhns_opt(df):
    wrap_rez={'opportunity':'', 'optimum_values':[], 'errors':[]}
    errors=list()
    all_rez=list()
    for k in range(20, 120, 1):
        for j in range(7, 50, 1):
            p=rhns(df, k, j, 0.05)
            if p['message']=='':
                pp=p['positions']
                if pp:
                    print(pp)
                else:
                    print('none')
                all_rez.append([calc(pp), k, j, 0.05])
            else:
                errors.append(p['message'])
    all_rez.sort(key=lambda kk: kk[0])
    #buiding the optimum values string
    wrap_rez['optimum_values']=','.join([str(all_rez[0][1]), str(all_rez[0][2]), str(all_rez[0][3])])
    opt_run=rhns(df, all_rez[0][1], all_rez[0][2], all_rez[0][3])
    wrap_rez['opportunity']=opt_run
    wrap_rez['errors']=errors
    return [wrap_rez, all_rez]

#UTILITIES
def calc(pp):
    r=1
    for i in pp:
        r=r*(1+i[2])
    r=r-1
    return r
