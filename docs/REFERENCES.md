# References

Primary sources the method and the T3 explanation tests (D-039) rely on. Quotes are copied from the pages listed (retrieved 1 Nov 2026). Where we rely on a claim, the quote is the exact text; we do not rely on anything not quoted here.

## MODIS and VIIRS active fire products

1. **Schroeder, W., Oliva, P., Giglio, L., Csiszar, I. A. (2014).** The New VIIRS 375 m active fire detection data product: Algorithm description and initial assessment. *Remote Sensing of Environment* 143, 85–96. doi:[10.1016/j.rse.2013.12.008](https://doi.org/10.1016/j.rse.2013.12.008). https://www.sciencedirect.com/science/article/abs/pii/S0034425713004483
   > "VIIRS 375m fire data showed significantly superior mapping capabilities compared to current MODIS fire detection data with improved consistency of fire perimeter delineation for biomass burning lasting multiple days."

   Used for: VIIRS 375 m counts are not on the MODIS scale, so a calibration factor is needed (PLAN §4).

2. **Giglio, L., Schroeder, W., Justice, C. O. (2016).** The collection 6 MODIS active fire detection algorithm and fire products. *Remote Sensing of Environment* 178, 31–41. doi:[10.1016/j.rse.2016.02.054](https://doi.org/10.1016/j.rse.2016.02.054). https://pmc.ncbi.nlm.nih.gov/articles/PMC6110110/
   Used for: the MODIS C6/C6.1 algorithm behind MCD14ML (citation only; no specific claim relied on).

3. **Vadrevu, K., Lasko, K. (2018).** Intercomparison of MODIS AQUA and VIIRS I-Band Fires and Emissions in an Agricultural Landscape—Implications for Air Pollution Research. *Remote Sensing* 10(7), 978. doi:[10.3390/rs10070978](https://doi.org/10.3390/rs10070978). https://www.mdpi.com/2072-4292/10/7/978
   > "we first compared the fire products from two different sensors, the Visible Infrared Imaging Radiometer Suite (VIIRS) 375 m active fire product (VNP14IMG) and Moderate Resolution Imaging Spectroradiometer (MODIS) 1 km fire product (MCD14ML) in an agricultural landscape, Punjab, India."
   > "Results revealed that VIIRS detected fires were higher by a factor of 4.8 compared to MODIS Aqua and Terra sensors. Further, VIIRS detected fires were higher by a factor of 6.5 than Aqua."

   Used for: an independent order-of-magnitude check on our Aqua→S-NPP factor in Indian Punjab (our 2013–21 window factors are in `docs/RESULTS_T3.md` A4; different period, window and filters, so not expected to match exactly).

4. **Li, F., Zhang, X., Kondragunta, S., Csiszar, I. (2018).** Comparison of fire radiative power estimates from VIIRS and MODIS observations. *Journal of Geophysical Research: Atmospheres* 123. doi:[10.1029/2017JD027823](https://doi.org/10.1029/2017JD027823). https://www.researchgate.net/publication/324566694_Comparison_of_fire_radiative_power_estimates_from_VIIRS_and_MODIS_observations
   > "The results indicate that the VIIRS fire characterization capability is similar across swath, whereas MODIS is strongly dependent on view zenith angle."

   Used for: day-to-day Aqua/S-NPP ratios depend on viewing geometry, which is why the T3 pre-drift Δ curve (fit on natural day-to-day Δ) is a weak instrument for Aqua's clock-time drift (RESULTS_T3 caveats).

## Punjab burning moved later in the day

5. **NASA Earth Observatory (15 Dec 2025).** New Timing for Stubble Burning in India (H. Jethva). https://science.nasa.gov/earth/earth-observatory/new-timing-for-stubble-burning-in-india/
   > "But in the past few years, stubble fires have occurred progressively later in the day, Jethva said. He identified the shift by analyzing observations from GEO-KOMPSAT-2A, a South Korean geostationary satellite launched in late 2018 that collects data every 10 minutes."
   > "Most stubble fires now happen between 4 p.m. and 6 p.m., he said, meaning that fire-monitoring systems that rely solely on MODIS, or similar sensors like VIIRS (Visible Infrared Imaging Radiometer Suite), miss many of the fires."

6. **Singh, N., Pradhan, R., Shukla, B. P., Pandya, M. R. (ISRO Space Applications Centre) (2025).** Evidence of shift in stubble burning timing over northwest India from geostationary satellite observations. *Current Science* 129(10), 921–923. doi:[10.18520/cs/v129/i10/921-923](https://doi.org/10.18520/cs/v129/i10/921-923). https://www.researchgate.net/publication/397905183
   > "Our analysis shows a gradual shift in peak fire activity from ∼13:30 IST in 2020 to ∼17:00 IST in 2024, to avoid detection by polar-orbiting satellites."

   Used for (5, 6): an independent, geostationary prior for explanation T. Our T3 test uses only polar-orbiter data and was not tuned to these reports. Not found/quoted: the iFOREST 2025 report (not retrieved; not relied on).

## Data DOIs (checked 1 Nov 2026)

| Product | DOI | Where checked | Status |
|---|---|---|---|
| VIIRS/NPP Active Fires 6-Min L2 Swath 375m V002 (VNP14IMG) | 10.5067/VIIRS/VNP14IMG.002 | https://www.earthdata.nasa.gov/data/catalog/lpcloud-vnp14img-002 | verified on official catalog page |
| VIIRS/JPSS1 Active Fires 6-Min L2 Swath 375m V002 (VJ114IMG) | 10.5067/VIIRS/VJ114IMG.002 | https://www.earthdata.nasa.gov/data/catalog/lpcloud-vj114img-002 ("Giglio, Louis. … NASA Land Processes Distributed Active Archive Center, 2024. doi:10.5067/VIIRS/VJ114IMG.002") | verified on official catalog page |
| MODIS C6.1 MCD14ML via FIRMS | 10.5067/FIRMS/MODIS/MCD14ML | FIRMS citation string; listed as a cited DOI in NASA citation records (https://access.earthdata.nasa.gov/citations/CIT3804242140-ESDIS) | partly verified: no product landing page found; doi.org unreachable from the workspace |
| FIRMS standard (SP) archive, VIIRS | none found | earthdata.nasa.gov FIRMS citation page returned 404 | **not verifiable**: no FIRMS-specific SP DOI found, and FIRMS pages checked do not state that SP files are collection V002 |

NRT DOIs (`10.5067/FIRMS/VIIRS/VNP14IMGT_NRT.002`, `…/VJ114IMGT_NRT.002`) apply to NRT data only.
