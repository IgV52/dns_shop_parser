# Модуль для парсинга dns-shop.ru

<br>
<details> 
<summary><b>Тех.данные</b></summary>
<br><b>Перед началом парсинга нужно получить cookie, способ получения cookie показан в example.py</b><br>
<b>Метод - get_all_links_product()</b>
<br>возвращает все ссылки на продукты из
<br>("https://www.dns-shop.ru/products1.xml","https://www.dns-shop.ru/products2.xml","https://www.dns-shop.ru/products3.xml")
<br>
<br>
<details>
<summary><b>schema</b></summary>

```
[
  "https://www.dns-shop.ru/product/5a74a34171b1ed20/videokarta-kfa2-geforce-rtx-3050-x-black-35nsl8md6yek/", 
  ..., 
  "https://www.dns-shop.ru/product/5a768842a2f48a5a/ibp-powercom-raptor-rpt-1500ap/"
]

```
</details>
<br><b>Метод - get_all_guid_product(<ожидает массив ссылок полученных из get_all_links_product>)</b>
<br>парсит guid из ссылок полученных ранее
<br>
<br>
<details>
<summary><b>schema</b></summary>

```
[
  {
    "url": "https://www.dns-shop.ru/product/ffeb03b0c5cbdb11/provodnaa-garnitura-pero-ep16-krasnyj/",
    "guid": "ffeb03b0-c5cb-4347-adaa-69694a6db11c"
  },
  ...,
  {
    "url": "https://www.dns-shop.ru/product/ffee54ccec1451e5/vodonagrevatel-elektriceskij-timberk-t-wss30-n41d-v/",
    "guid": "ffee54cc-ec14-4ebf-b7ba-5306afd51e56"
  },
]

```
</details>
<br><b>Метод - get_all_info_product(<ожидает массив полученный из get_all_guid_product>)</b>
<br>парсит информацию о товаре
<br>
<br>
<details>
<summary><b>schema</b></summary>

```
[
  {
    "url": "https://www.dns-shop.ru/product/0000069528dbed20/zerkalnyj-fotoapparat-canon-eos-6d-mark-ii-body-cernyj/",
    "guid": "00000695-28db-11ed-9010-00155d8ed20b",
    "sku": "5068857",
    "brand": "Canon",
    "images": [
      "https://c.dns-shop.ru/thumb/st1/fit/300/300/bdf28d7702de838d1a8aafa7e100599d/74cddf19c5b1d48939e7c2261f5070fb8bc5661c27a451d26f8aeef3a5c0b073.jpg",
      "https://c.dns-shop.ru/thumb/st4/fit/300/300/045f7d10cd4f17803ac56daf3fb2e5bb/ec8e745bfb5577b4f7b1f3f0455187cf4a76c9d6740f29b488e8ae359026c73e.jpg",
      "https://c.dns-shop.ru/thumb/st4/fit/300/300/bd7911b37d76c40b4b7923cbd2adfa2d/58bbdc39958ff4ba328e0edc456182d84e0e27a2ad5447d00d9b86b1269cf026.jpg"
    ],
    "price": 134999,
    "name": "Зеркальный фотоаппарат Canon EOS 6D Mark II Body черный",
    "description": "Зеркальная камера Canon EOS 6D Mark II Body подходит для фотографов, знакомых с композицией работы со светом и важными нюансами в области фотографии. Она выполнена в компактном корпусе с защитой от влаги и пыли, содержит GPS-приемник для фиксации перемещений. Вы сможете присваивать каждому снимку геотеги, где бы вы ни находились. \nДля создания портретных фото с малой глубиной резкости Canon EOS 6D Mark II Body задействует полнокадровый датчик с его способностью улавливать даже мимолетные выражения лица. Датчик CMOS с поддержкой 27.1 Мп и чувствительностью 100-40000 ISO позволяет создавать динамичные изображения с многочисленными мелкими деталями при пейзажной съемке. Аппарат осуществляет серийную съемку со скоростью 6.5 кадр./сек. \nИсключительную резкость снимков обеспечивают широкие возможности автофокусировки. Вы можете создавать шедевральные фото при лунном свете, а также, работая с небольшой глубиной резкости, отслеживая движущиеся объекты. Благодаря большому видоискателю процесс съемки будет легким и интуитивным."
  },
  ...,
  {
    "url": "https://www.dns-shop.ru/product/0001cb51565ded20/velosiped-hiper-hb-0017-sinij/",
    "guid": "0001cb51-565d-11ed-9041-00155d8ed20c",
    "sku": "5081873",
    "brand": "HIPER",
    "images": [
      "https://c.dns-shop.ru/thumb/st4/fit/300/300/d5598d61800ba4860ca297f16304cc48/6d57bb3cfbe5a10d0eeff3421e01ea713f2eb001408cf79edaea5901164ab3df.jpg",
      "https://c.dns-shop.ru/thumb/st1/fit/300/300/5f0973717177dcbe15effe9645884236/b95142f14eacab0ee617d283f295e605f57520e22b745547880002efdf095cf7.jpg",
      "https://c.dns-shop.ru/thumb/st1/fit/300/300/e992862a1a1f2af12f1df8ecf9e4dd84/ea5bf130e6575936c1b13661f0c23cd9941414b57a1ddc8b47497d2da2927c86.jpg"
    ],
    "price": 14199,
    "name": "Велосипед HIPER HB-0017 синий",
    "description": "Велосипед HIPER HB-0017 синего цвета имеет складную конструкцию, что позволяет легко перевозить его в багажном отсеке авто. В складном виде удобно хранить транспорт в зимнее время. На стальной раме закреплен LED-фонарь, что позволяет комфортно и безопасно передвигаться в темное время. Для его питания используется аккумулятор емкостью 5000 мА·ч. Велосипед выдерживает нагрузку до 100 кг. \nHIPER HB-0017 с диаметром колес 26\" подходит для катания по грунтовым и асфальтовым дорогам. Они позволяют быстро разогнаться, но не подходят для езды на высоких скоростях. Благодаря навесному оборудованию SHIMANO вы получаете качественную трансмиссию. В зависимости от наклона система подбирает оптимальную скорость: предусмотрен 21 скоростной режим. Для мгновенной остановки движения предусмотрены дисковые задние и передние тормоза. Даже в плохую погоду транспорт останавливается очень быстро. Модель подходит для долгого катания, поскольку использует эргономичное седло, удобные педали."
  },
]
```

</details>
<br>
<b>Примерное время парсинга всех товаров ~2 час +- 20минут</b>
</details> 
<br>
<br>
<details> 
<summary><b>Установка из образа докера</b></summary>

```
git clone repo
docker build -f Dockerfile -t dns_shop_parser .
>> other Dockerfile
COPY --from=module_dns_shop_parser /wheels/ /
RUN pip install /dns_shop_parser-0.1-py3-none-any.whl
```