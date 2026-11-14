# Independent recount of RAW masked/filtered monthly counts per platform for sample districts.
# Does not import blindspot code. Rules from CLAUDE.md: standard data, type==0, MODIS conf>=30,
# VIIRS conf n/h, persistent mask (0.01 deg cell), local solar month.
import duckdb, json, random
random.seed(20261102)
IDX = json.load(open('web/public/data/index.json'))['districts']
names = {d['name']: d['id'] for d in IDX if d['country'] in ('PAK', 'IND')}
pick = []
for want in ['Lahore', 'Sangrur', 'Kasur']:
    pick += [d for d in IDX if d['name'] == want][:1]
pick += random.sample([d for d in IDX if d['name'] not in ('Lahore', 'Sangrur', 'Kasur')], 4)
con = duckdb.connect()
con.sql("""create view h as select platform, lat, lon, processing, type, confidence_raw,
  cast(local_solar_datetime as date) d from read_parquet('data/processed/hotspots/**/*.parquet', hive_partitioning=true)""")
con.sql("create view m as select cell_lat, cell_lon from 'data/processed/persistent_mask_cells.parquet'")
con.sql("create view pr as select lat, lon, shape_id from 'data/processed/regions/point_regions.parquet' where level='ADM2'")
tot = bad = 0
for d in pick:
    j = json.load(open(f"web/public/data/districts/{d['id']}.json"))
    rows = con.execute("""
      select h.platform, year(h.d)*12+month(h.d)-1 as mi, count(*)
      from h join pr on pr.lat=h.lat and pr.lon=h.lon and pr.shape_id=?
      where h.processing='standard' and h.type=0
        and ((h.platform in ('Terra','Aqua') and try_cast(h.confidence_raw as int)>=30)
          or (h.platform in ('SNPP','NOAA20') and h.confidence_raw in ('n','h')))
        and not exists (select 1 from m where m.cell_lat=cast(floor(h.lat*100+1e-6) as bigint)
                                          and m.cell_lon=cast(floor(h.lon*100+1e-6) as bigint))
      group by 1,2""", [d['id']]).fetchall()
    mine = {}
    for p, mi, n in rows: mine[(p, mi)] = n
    first = 2003 * 12
    mism = []
    for plat, obj in j['raw'].items():
        key = {'S-NPP': 'SNPP', 'NOAA-20': 'NOAA20'}.get(plat, plat)
        for i, n in enumerate(obj['n']):
            theirs = n or 0
            ours = mine.get((key, first + i), 0)
            tot += 1
            if theirs != ours:
                bad += 1; mism.append((plat, 2003 + i // 12, i % 12 + 1, theirs, ours))
    print(d['name'], d['country'], 'platforms', list(j['raw'].keys()), 'mismatches', len(mism), mism[:4])
print('cells compared', tot, 'mismatched', bad)
