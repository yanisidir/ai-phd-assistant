from processing.parser import cleanup_low_score_offers, init_db, save_offer_without_ai

from scraping.crawl4ai_inspirehep import get_offers as get_inspirehep_offers
from scraping.crawl4ai_academic_positions import get_offers as get_academic_positions_offers


def main():
    init_db()
    cleanup_low_score_offers()

    all_offers = []

    print("\n=== InspireHEP ===")
    inspire_offers = get_inspirehep_offers(max_offers=5, query="phd")
    print("[DEBUG main] InspireHEP retourne", len(inspire_offers), "offres")
    all_offers.extend(inspire_offers)

    print("\n=== Academic Positions ===")
    academic_offers = get_academic_positions_offers(max_offers=5)
    print("[DEBUG main] Academic Positions retourne", len(academic_offers), "offres")
    all_offers.extend(academic_offers)

    seen_links = set()
    unique_offers = []

    for offer in all_offers:
        link = offer.get("link", "")

        if link in seen_links:
            continue

        seen_links.add(link)
        unique_offers.append(offer)

    print("\nNombre total d'offres uniques :", len(unique_offers))

    for offer in unique_offers:
        print("=" * 80)
        print("Source :", offer.get("source", ""))
        print("Titre :", offer.get("title", ""))
        print("Lien :", offer.get("link", ""))
        print("Laboratoire :", offer.get("laboratory", ""))
        print("Localisation :", offer.get("location", ""))
        print("Deadline :", offer.get("deadline", ""))
        print("Contact :", offer.get("contact", ""))
        print("Description :", offer.get("description", "")[:400], "...")
        print("-" * 80)

        saved = save_offer_without_ai(offer)

        if saved:
            print("Offre sauvegardée sans LLM")
        else:
            print("Offre ignorée non sauvegardée")
        print("=" * 80)


if __name__ == "__main__":
    main()
