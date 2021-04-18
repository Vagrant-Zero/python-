"""二手房数据爬取
   数据分析展示
"""

import requests
from lxml import etree
import time
import random
from pyecharts import options as opts
from pyecharts.charts import Map
from pyecharts.charts import Geo
from pyecharts.globals import ChartType, SymbolType, GeoType
import json


def get_html_text(url):
    try:
        print('正在获取数据，请稍等......')
        headers = {
            'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36 Edg/89.0.774.63'
        }
        r = requests.get(url, headers = headers, timeout = 5)
        r.raise_for_status()
        print('数据获取完毕！')
        return r.text
    except:
        print('爬取失败')
        return ' '

# 解析数据
def get_data(html_text):
    title = []
    price = []
    Area = []
    style = []
    location = []
    rigion = []
    tree = etree.HTML(html_text)
    div_list = tree.xpath('//*[@id="__layout"]/div/section/section[3]/section[1]/section[2]/div[@class = "property"]')
    for div in div_list:
        title.append(div.xpath('./a/div[2]/div[1]/div[1]/h3/text()')[0])                                                              # 房屋名字
        house_style_span_list = div.xpath('./a/div[2]/div[1]/section/div[1]/p[1]/span')                                              # 房屋样式
        house_style = ''
        for span in house_style_span_list:
            house_style += span.xpath('./text()')[0]
        style.append(house_style)
        Area.append(div.xpath('./a/div[2]/div[1]/section/div[1]/p[2]/text()')[0].strip())                                            # 房屋面积
        house_location = {
            'community_name' : div.xpath('./a/div[2]/div[1]/section/div[2]/p[1]/text()')[0]
        }
        detail_location = ''
        detail_location_list  = div.xpath('./a/div[2]/div[1]/section/div[2]/p[2]/span')
        rigion.append(detail_location_list[0].xpath('./text()')[0] + '区')                                                               # 所属区域
        for span in detail_location_list:
            detail_location += span.xpath('./text()')[0]
        house_location['detail_location'] = detail_location
        location.append(house_location)                                                                                                    # 房屋位置
        price.append(div.xpath('./a/div[2]/div[2]/p[1]/span[1]/text()')[0])                                                           # 房屋价格
    return title, price, Area, style, rigion, location

def save_data(title, price, Area, style, location):
    print('数据存储中，请稍等......')
    with open('二手房数据.txt', 'w') as fp:
        for i in range(len(title)):
            fp.write(title[i] + '\n')
            fp.write(price[i] + ',')
            fp.write(Area[i] + ',')
            fp.write(style[i] + '\n')
            fp.write(str(location[i]) + '\n')
    fp.close()
    print('数据存储完毕，请到指定目录查看！')

# 采用浏览器端方式获取经纬度
def getPosition(ak, dw):
    url = 'http://api.map.baidu.com/geocoding/v3/?address={Address}&output=json&ak={Ak}'.format(Address=dw, Ak=ak)
    res = requests.get(url)
    json_data = json.loads(res.text)
    if json_data['status'] == 0:
        lat = json_data['result']['location']['lat']  # 纬度
        lng = json_data['result']['location']['lng']  # 经度
    else:
        print("Error output!")
        print(json_data)
        return json_data['status']
    return lat,lng

def draw_map(data_pair, data_coordinate) -> Geo:   # ->常常出现在python函数定义的函数名后面，为函数添加元数据,描述函数的返回类型，从而方便开发人员使用。
    g = Geo()
    # 选择要显示的地图
    g.add_schema(maptype="重庆", center=[106.531638,29.561081], itemstyle_opts=opts.ItemStyleOpts(color="#575D57"))
    # 使用add_coordinate(name, lng, lat)添加坐标点和坐标名称
    for item in data_coordinate:
        g.add_coordinate(item['name'], item['lng'], item['lat'])
    # 将数据添加到定义的地图上
    g.add('', data_pair, type_=GeoType.EFFECT_SCATTER, symbol_size=5)                         # type_=ChartType.HEATMAP
    # 设置样式
    g.set_series_opts(label_opts=opts.LabelOpts(is_show=False))\
                                     .set_global_opts(visualmap_opts=opts.VisualMapOpts(min_=60, max_ = 200, is_piecewise=True),title_opts=opts.TitleOpts(title="重庆房源分布图"))
    return g

if __name__ == '__main__':
    url = 'https://cq.58.com/ershoufang/'
    '''获取数据'''
    page_text = get_html_text(url)
    time.sleep(random.randint(3, 10))
    title, price, Area, style, rigion, location = get_data(page_text)
    save_data(title, price, Area, style, location)
    '''分析数据'''
    data= []
    coordinate = []
    ak = '你的AK'
    for i in range(len(rigion)):
        single_coordinate = {
            'name' : location[i]['community_name']
        }
        dw = '重庆市' + location[i]['detail_location']
        lat, lng = getPosition(ak, dw)
        single_coordinate['lng'] = lng
        single_coordinate['lat'] = lat
        coordinate.append(single_coordinate)
        data.append((location[i]['community_name'], eval(price[i])))                           # 一间房屋区域 & 价格
    # 绘制房价分布地图
    CQ_map = draw_map(data, coordinate)
    CQ_map.render(path="重庆房源分布.html")
