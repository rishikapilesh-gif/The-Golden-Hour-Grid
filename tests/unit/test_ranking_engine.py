from backend.app.models.incident import Incident
from backend.app.providers.routing.demo_router import DemoRoutingProvider
from backend.app.ranking.engine import DeterministicRankingEngine


def test_ranking_deterministic_and_gender_invariance(seed_test_data):
    router = DemoRoutingProvider()
    engine = DeterministicRankingEngine(router)

    hospitals = [
        seed_test_data["hospital_1"],
        seed_test_data["hospital_2"],
        seed_test_data["hospital_closed"]
    ]

    # Create baseline incident
    inc_male = Incident(
        id="test-inc-1",
        location_label="Central Junction",
        latitude=300.0,
        longitude=150.0,
        injury_category="trauma",
        incident_source="Road traffic collision",
        gender="Male",
        reported_priority="Critical",
        witness_assessment="Critical",
        heart_rate_bpm=118,
        spo2_percent=92.0,
        reported_blood_group="O-",
        route_hazards=[]
    )

    ranking_male = engine.rank_hospitals(inc_male, hospitals)

    # Rank 1 must be eligible with highest score
    assert ranking_male.recommendations[0].rank == 1
    assert ranking_male.recommendations[0].score > ranking_male.recommendations[1].score
    assert ranking_male.recommendations[0].eligible is True

    # Closed hospital must be ineligible with score 0
    closed_rec = next(r for r in ranking_male.recommendations if r.hospital_id == "demo-hospital-closed")
    assert closed_rec.score == 0
    assert closed_rec.eligible is False

    # Test GENDER INVARIANCE across Female, Unknown, Other
    for test_gender in ["Female", "Unknown", "Other / not stated"]:
        inc_test = Incident(
            id=f"test-inc-{test_gender}",
            location_label="Central Junction",
            latitude=300.0,
            longitude=150.0,
            injury_category="trauma",
            incident_source="Road traffic collision",
            gender=test_gender,
            reported_priority="Critical",
            witness_assessment="Critical",
            heart_rate_bpm=118,
            spo2_percent=92.0,
            reported_blood_group="O-",
            route_hazards=[]
        )
        ranking_test = engine.rank_hospitals(inc_test, hospitals)

        # Scores and ranks must be 100% identical!
        for rec_m, rec_t in zip(ranking_male.recommendations, ranking_test.recommendations):
            assert rec_m.hospital_id == rec_t.hospital_id
            assert rec_m.rank == rec_t.rank
            assert rec_m.score == rec_t.score
            assert rec_m.components.travel == rec_t.components.travel
            assert rec_m.components.specialist == rec_t.components.specialist
            assert rec_m.components.icu == rec_t.components.icu


def test_ranking_vitals_warning(seed_test_data):
    router = DemoRoutingProvider()
    engine = DeterministicRankingEngine(router)

    hospitals = [seed_test_data["hospital_1"]]

    # Incident with severe SpO2 drop (85%)
    inc_low_spo2 = Incident(
        id="test-inc-spo2",
        location_label="Central Junction",
        injury_category="trauma",
        incident_source="Road traffic collision",
        gender="Unknown",
        reported_priority="Critical",
        witness_assessment="Critical",
        heart_rate_bpm=140,
        spo2_percent=85.0,
        reported_blood_group="O-",
        route_hazards=[]
    )

    ranking = engine.rank_hospitals(inc_low_spo2, hospitals)
    rec = ranking.recommendations[0]

    # Must contain warning for qualified clinician review requirement
    assert any("clinician review" in w for w in rec.warnings)
