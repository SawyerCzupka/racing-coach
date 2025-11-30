from fastapi import APIRouter

router = APIRouter()


@router.get("/core-test")
def test_core():
    from racing_coach_core._rs import hello_from_rust

    return hello_from_rust()
