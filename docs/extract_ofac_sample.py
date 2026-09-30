import xml.etree.ElementTree as ET, csv, os
NS = "{https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/ADVANCED_XML}"
root = ET.parse("SDN_ADVANCED.XML").getroot()
ftypes = {f.get("ID"): f.text for f in root.iter(NS+"FeatureType")
          if (f.text or "").startswith("Digital Currency Address")}
print("Currency types found:", sorted(v.split(" - ")[-1] for v in ftypes.values()))
per_ccy, rows, keep = {}, [], []
for p in root.iter(NS+"DistinctParty"):
    hits = [(ftypes[f.get("FeatureTypeID")], v.text)
            for f in p.iter(NS+"Feature") if f.get("FeatureTypeID") in ftypes
            for v in f.iter(NS+"VersionDetail")]
    if not hits: continue
    ccy = hits[0][0].split(" - ")[-1]
    if per_ccy.get(ccy, 0) >= 2 or len(keep) >= 18: continue
    per_ccy[ccy] = per_ccy.get(ccy, 0) + 1
    keep.append(p)
    name = next((n.text for n in p.iter(NS+"NamePartValue")), "")
    rows += [(p.get("FixedRef"), name, c.split(" - ")[-1], a) for c, a in hits]
os.makedirs("research", exist_ok=True)
out = ET.Element("SampleFragment")
for k, v in ftypes.items():
    ET.SubElement(out, "FeatureType", ID=k).text = v
for p in keep: out.append(p)
ET.ElementTree(out).write("research/ofac_sample.xml", encoding="utf-8")
with open("research/ofac_sample.csv", "w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows([("fixed_ref", "name", "currency", "address")] + rows)
print("Per currency:", per_ccy, "| rows:", len(rows))