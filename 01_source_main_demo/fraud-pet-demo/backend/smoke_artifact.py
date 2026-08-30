import sys
from fastapi.testclient import TestClient
from app.main import create_app
app = create_app(database_url="sqlite:///./data/smoke_art.sqlite")
c = TestClient(app)
SID = "art_user"
c.post("/api/learning/goals", json={"ownerId":SID,"title":"反诈","theme":"反诈","periodDays":7,"dailyMinutes":20,"expectedOutcome":"能识别常见诈骗并正确处置","difficulty":"入门","summary":"x","electiveTracks":["a"]})
d = c.get(f"/api/learning/dashboard?ownerId={SID}").json()
pid = d["plan"]["id"]
r = c.post("/api/learning/artifacts", json={"ownerId":SID,"planId":pid,"title":"我的反诈海报","artifactType":"poster","visibility":"public","contentSummary":"展示了三类高危信号及核验方法"})
print("artifact create", r.status_code)
assert r.status_code == 200, r.text
aid = r.json()["id"]
r = c.post(f"/api/learning/artifacts/{aid}/review", json={"ownerId":SID,"contentSummary":"V1 展示三类高危信号及核验方法","attachmentRefs":[]})
print("artifact review", r.status_code, r.json().get("score"), r.json().get("passFlag"), r.json().get("source"))
assert r.status_code == 200 and "score" in r.json()
r = c.post(f"/api/learning/artifacts/{aid}/versions", json={"ownerId":SID,"contentSummary":"V1 展示三类高危信号及核验方法","attachmentRefs":[]})
print("artifact version(submit+review)", r.status_code)
assert r.status_code == 200
print("ARTIFACT+REVIEW OK")
