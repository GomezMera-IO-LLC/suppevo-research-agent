#!/usr/bin/env python3
"""Resolve remaining BulkSupplements products without images by trying Shopify handles."""
import json
import urllib.request
import urllib.error
import time

SHOPIFY_BASE = "https://www.bulksupplements.com"

# Products without images and their likely Shopify handles
HANDLE_MAP = {
    "2cfbbb44-9f2c-4e7a-9887-be5503f579c7": "acetyl-l-carnitine-alcar",  # ALCAR 600mg
    "9ea3b98d-4316-46dc-bc79-da7b1e5cf3a5": "acai-berry-capsules",  # Acai Berry 400mg
    "b6c88b69-609e-4f83-a199-0c2875917a27": "acai-berry-capsules",  # Acai Berry Extract
    "05d412e9-37f2-4732-ae28-3b1eb5c24605": "acerola-extract",  # Acerola Extract
    "2d42c0bc-ec02-4976-80e0-a40dc7b4b210": "apple-powder",  # Apple Powder
    "0898f7ec-91e3-4a72-9194-4f2979d59549": "bamboo-extract",  # Bamboo Extract
    "06076f8c-efbb-48da-b088-8cb2bf77f5a6": "barley-grass-powder",  # Barley Extract
    "2da636c7-401d-44e3-96dc-e9e29323a80c": "beet-root-powder",  # Beet Root Powder
    "2de690f2-b3a9-43bb-a521-117b83992bf7": "blueberry-extract",  # Blueberry Extract
    "f6f1ffec-ecd7-45b5-b1d4-38b6118ae196": "caffeine-pills",  # Caffeine 200mg
    "067a5380-8f13-4c30-b725-83f8b70b5e44": "cayenne-pepper-extract-powder",  # Cayenne Extract
    "a8e7618e-d29c-4ad8-b58f-b0aaf1af5cbb": "cayenne-pepper-extract-powder",  # Cayenne Extract 500mg
    "2c1f6774-04a3-447c-a8dc-f4fa76e7ebe3": "chamomile-extract-powder",  # Chamomile Extract
    "5ed8e13d-a67d-4a9d-b584-a45f2a2085d8": "chicory-root-extract",  # Chicory Extract
    "6a48171b-3155-42f2-9de9-22f6d0e9bc10": "choline-l-bitartrate",  # Choline DL-Bitartrate
    "2fb444ad-b9a8-4bbd-ad9f-a14f9614b6a9": "choline-l-bitartrate",  # Choline DL-Bitartrate 600mg
    "99ae14e7-b98a-4166-9746-42ce63d86cb0": "cnidium-monnieri-extract",  # Cnidium Extract
    "ffef8287-3ccf-4f37-aa03-f27c2a9b9acb": None,  # Creatine HCL - DISCONTINUED
    "9b2e8113-9604-4f6e-bd5d-dae41c3c1049": "creatinol-o-phosphate",  # Creatinol o-Phosphate
    "0ed7df2a-b8b0-4184-a6a7-9f8c92ffb344": "dmae-bitartrate-powder",  # DMAE Bitartrate
    "455cd1cc-a4eb-4395-a12b-4b1e89bb0b71": "dong-quai-extract",  # Dong Quai Extract
    "556a6da2-00b0-4dcf-ba96-605b47bf5b4d": "calcium-disodium-edta-powder",  # EDTA Disodium
    "05a52b9a-538d-4189-9c8c-8f060884e950": "galla-chinensis-extract",  # Galla Chinensis
    "9334df5f-a7e5-4a0f-8d21-71b754c97581": "gaba-gamma-aminobutyric-acid-powder",  # GABA
    "4065721c-599d-4899-bc3e-e0d1152121b9": "gaba-gamma-aminobutyric-acid-powder",  # GABA 600mg
    "8e15f2d1-d8e0-4a63-abe2-5d795b5474c8": "garcinia-cambogia-extract",  # Garcinia 60% HCA
    "0da5c7fc-7d79-496a-ae1a-0b019fad0c61": "garcinia-cambogia-extract",  # Garcinia 60% 500mg
    "08872c4b-3767-4bec-9f2f-0c85c92f4cc4": "garcinia-cambogia-extract",  # Garcinia 50% HCA
    "44e4cc0b-4e54-426e-9ef9-9200f969dff2": "glutathione-reduced-powder",  # Glutathione
    "447bd085-8889-4642-8282-3335a69efb54": "glutathione-reduced-powder",  # Glutathione 500mg
    "989de83b-5a40-422d-8957-495ab2a41c3a": "goji-berry-extract",  # Goji Powder
    "237a1ea8-8158-4043-ac6d-debc6c747361": "grass-fed-whey-protein-isolate-powder",  # Grass-Fed Whey
    "3f3c25c2-97f0-4cfb-b6b2-790820da7119": "graviola-extract",  # Guanabana Extract
    "419d4776-ea33-4f37-9fa6-05e84693eccb": "horsetail-extract",  # Horsetail P.E
    "12db315b-3d90-434a-a18e-636ae4f73710": "inulin-powder",  # Inulin
    "1375ef47-b3e1-49a5-ac54-37fbd9275314": "konjac-root-extract-powder",  # Konjac Root
    "5f28b82b-c3fd-4aa8-9f9b-0814dc581afe": "kudzu-root-extract",  # Kudzu Root
    "6d561626-bcbc-42ab-a6fb-004f34b854d2": "l-arginine-base",  # L-Arginine 500mg
    "568bbf85-7c92-40c8-a8e5-fa7eaa93a960": "l-ornithine-alpha-ketoglutarate",  # L-Ornithine AKG
    "097ab4dd-cd96-453f-a0fc-b7e44e9d7d41": "soy-lecithin-powder",  # Lecithin Powder
    "16652109-8cca-4071-a8ce-4eae363c19e9": "lecithin-softgels",  # Lecithin Softgel 1200mg
    "6a153771-119f-42ed-96de-0172b5685c89": "lecithin-softgels",  # Lecithin Softgels (1200mg)
    "80b5c970-de84-444e-a85b-62402a0b580d": "lemon-juice-powder",  # Lemon Powder
    "c1ff873e-ad5d-4182-98ad-19dd4a635601": "licorice-root-extract",  # Licorice Root Extract
    "30b1e4dd-3260-4851-be3b-06e6bf65381e": "lions-mane-mushroom-extract",  # Lion's Mane
    "7829bf9a-8b66-444b-acb2-a89ba0764692": "maca-root-extract",  # Maca Root Extract
    "e6063405-91df-4497-85ee-485f2014061d": "maca-root-extract",  # Maca Root Extract 500mg
    "41b25784-e561-4720-93a4-cfa2be77bd1e": "mango-powder",  # Mango Powder
    "8418f6b4-57a9-4075-a718-6e403a6bdd08": "motherwort-extract",  # Motherwort
    "40a30305-bea5-4957-808c-214d88c858a4": "nattokinase-powder",  # Nattokinase
    "139ed7b3-d2f3-48c8-b85d-87ad77e7ac77": "papaya-leaf-extract",  # Papaya Fruit Extract
    "0ab5150f-654c-43b6-ac9d-59d7502c4104": "pineapple-powder",  # Pineapple Powder
    "28e9ed13-61d5-473e-bbee-534e82057d6b": "plantain-leaf-extract-powder",  # Plantain Leaf
    "0c98cbaa-4d35-4799-93d4-46d0147dfc42": "pomegranate-extract-powder",  # Pomegranate
    "7e83c6df-571f-4bd2-b30e-bc35676a036d": "psyllium-husk",  # Psyllium Husk 500mg
    "3ad2bd49-a47e-4e4d-8aa0-85b4d6690a1f": "glutathione-reduced-powder",  # Reduced Glutathione
    "44b44b51-acec-4097-840a-a3209d655446": "rosehip-extract",  # Rosehip Extract
    "4d8a3942-3890-428a-ad19-deff525ff31d": "sea-buckthorn-powder",  # Sea Buckthorn
    "0f3628b8-5482-4142-b4fe-3c9ff1ec87ef": "slippery-elm-bark-extract",  # Slippery Elm
    "097f3f86-9a46-486c-b829-ee66049a0bb1": "sodium-bhb-beta-hydroxybutyrate",  # Sodium BHB
    "2379024d-dda4-4ab1-873d-aab90324d3e0": "soy-isoflavones-powder",  # Soy Isoflavones
    "5d19d47c-5e54-4aba-b0c4-d2b6fd8ac9d9": "spinach-extract",  # Spinach Extract
    "32bc4383-3701-4e75-9a31-f3f1d858a4d7": "spirulina-powder",  # Spirulina
    "a1ed1cf8-30f1-47c7-b0f0-bdfebd68589b": "strawberry-powder",  # Strawberry Powder
    "269e1c09-d526-4b49-b674-1ecba426afe5": "sulbutiamine-powder",  # Sulbutiamine
    "67340483-2f01-40f2-9888-999bc1cee304": "triphala-powder",  # Triphala
    "82d63b0b-1a9c-443f-a381-84c3cff19949": "uva-ursi-extract",  # Uva Ursi
    "25bac16c-6109-4cee-944e-f6f83290f54f": "niacin-vitamin-b3-powder",  # Vitamin B3
    "9edcc9a3-9273-4fe3-8fa0-d68eaeda252d": "pantothenic-acid-vitamin-b5-powder",  # Vitamin B5
}


def fetch_shopify_image(handle):
    """Get the main product image from Shopify JSON API."""
    url = f"{SHOPIFY_BASE}/products/{handle}.json"
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            product = data.get("product", {})
            images = product.get("images", [])
            if images:
                return images[0].get("src")
            # Try variant featured image
            for v in product.get("variants", []):
                fi = v.get("featured_image")
                if fi and fi.get("src"):
                    return fi["src"]
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print(f"  Rate limited, waiting 10s...")
            time.sleep(10)
            return fetch_shopify_image(handle)
        return None
    except Exception:
        return None
    return None


def main():
    matched = []
    failed = []
    discontinued = []

    total = len(HANDLE_MAP)
    for i, (product_id, handle) in enumerate(HANDLE_MAP.items()):
        if handle is None:
            discontinued.append(product_id)
            print(f"  [{i+1}/{total}] DISCONTINUED: {product_id}")
            continue

        time.sleep(2.0)  # Avoid rate limiting
        image_url = fetch_shopify_image(handle)

        if image_url:
            matched.append({"id": product_id, "imageUrl": image_url})
            print(f"  [{i+1}/{total}] ✅ {handle} -> found image")
        else:
            failed.append({"id": product_id, "handle": handle})
            print(f"  [{i+1}/{total}] ❌ {handle} -> no image found")

    print(f"\n{'='*60}")
    print(f"RESULTS")
    print(f"{'='*60}")
    print(f"Matched: {len(matched)}")
    print(f"Failed: {len(failed)}")
    print(f"Discontinued: {len(discontinued)}")

    # Save results
    output = {
        "matched": matched,
        "failed": failed,
        "discontinued": discontinued,
    }
    with open("scripts/bulksupplements_remaining_batch.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved to scripts/bulksupplements_remaining_batch.json")

    # Also save batch update format
    if matched:
        batches = []
        for i in range(0, len(matched), 25):
            batches.append(matched[i:i+25])
        with open("scripts/bulksupplements_remaining_update_batches.json", "w") as f:
            json.dump(batches, f, indent=2)
        print(f"Update batches ({len(batches)}): scripts/bulksupplements_remaining_update_batches.json")


if __name__ == "__main__":
    main()
