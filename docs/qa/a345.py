import duckdb, json, glob, math
con=duckdb.connect()
H="read_parquet('data/processed/hotspots/**/*.parquet', hive_partitioning=true)"
# A3: harmonized sanity over all district + region JSON
neg=nan=big=0; n=0; maxv=0
for f in glob.glob('web/public/data/districts/*.json')+glob.glob('web/public/data/regions/*.json'):
    j=json.load(open(f))
    for k in ('value','lo','hi'):
        for x in j['harmonized'][k]:
            if x is None: continue
            n+=1
            if isinstance(x,float) and math.isnan(x): nan+=1
            elif x<0: neg+=1
            maxv=max(maxv,x)
print('A3 values checked',n,'negative',neg,'nan',nan,'max',maxv)
fac=con.sql("select min(factor) lo,max(factor) hi,count(*) n from (select * from 'data/processed/harmonized/calibration_factors.parquet')").fetchall() if False else None
print('A3 factor columns',con.sql("describe select * from 'data/processed/harmonized/calibration_factors.parquet'").fetchall()[:8])
# A4: share of filtered S-NPP detections removed by mask
q=f"""with f as (select platform,lat,lon from {H} where processing='standard' and type=0 and (
   (platform in ('Terra','Aqua') and try_cast(confidence_raw as int)>=30) or (platform in ('SNPP','NOAA20') and confidence_raw in ('n','h')))),
 t as (select platform, count(*) n, sum(case when exists(select 1 from 'data/processed/persistent_mask_cells.parquet' m where m.cell_lat=cast(floor(f.lat*100+1e-6) as bigint) and m.cell_lon=cast(floor(f.lon*100+1e-6) as bigint)) then 1 else 0 end) masked from f group by 1)
 select platform,n,masked,round(100.0*masked/n,2) from t order by 1"""
print('A4 (platform, filtered, masked, % masked):',con.sql(q).fetchall())
mr=json.load(open('data/processed/mask_report.json')); print('A4 mask_report keys',list(mr)[:12])
# A5: local solar date = UTC + lon/15 h ? and first-day coverage
q=f"""select max(abs(epoch(local_solar_datetime)-(epoch(acq_datetime_utc)+lon/15.0*3600))) from {H} using sample 200000 rows"""
try: print('A5 max |local - (utc+lon/15h)| seconds (sample):',con.sql(q).fetchall())
except Exception as e: print('A5 sample query failed',str(e)[:200])
q=f"""select platform, cast(local_solar_datetime as date) d, count(*) from {H}
 where cast(local_solar_datetime as date) between date '2003-01-01' and date '2003-01-04' and platform in ('Terra','Aqua') group by 1,2 order by 1,2"""
print('A5 first days 2003 (Terra/Aqua):',con.sql(q).fetchall())
q=f"""select min(year), max(year) from {H}"""; print('A5 file-year range',con.sql(q).fetchall())
