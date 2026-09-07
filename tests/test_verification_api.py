import socket
import threading
import time
import httpx
import uvicorn
from qds_protocol.key_distribution import distribute
from qds_protocol.signing_engine import sign
from qds_protocol.verification_engine import VerificationEngine
from quantum_core.bell_state_generator import sample_chsh
from presentation.security_event_log import SecurityEventLog
from presentation.verification_api import create_app

def test_http(tmp_path):
    d=distribute(512,7);p,r=sign(d,'real HTTP signature',.1,8)
    v=VerificationEngine();v.register(d,r);log=SecurityEventLog(tmp_path/'events.jsonl')
    app=create_app(v,{d.session_id:sample_chsh(2048,.1,9)},log,.045,.2)
    sock=socket.socket();sock.bind(('127.0.0.1',0));sock.listen(128);port=sock.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(app,log_level='error'))
    thread=threading.Thread(target=server.run,kwargs={'sockets':[sock]},daemon=True);thread.start()
    try:
        for _ in range(100):
            if server.started:break
            time.sleep(.02)
        assert server.started
        response=httpx.post(f'http://127.0.0.1:{port}/verify',json=p.model_dump())
        print('Real HTTP status/report:',response.status_code,response.json()['decision'],response.json()['qber'])
        assert response.status_code==200 and response.json()['decision']=='ACCEPT'
        assert httpx.post(f'http://127.0.0.1:{port}/verify',json=p.model_dump()).json()['attribution']['attack_class']=='replay'
        assert len(log.read())==2

        # Verify dashboard and simulation API endpoints
        status_res = httpx.get(f'http://127.0.0.1:{port}/api/status')
        assert status_res.status_code == 200
        assert status_res.json()['status'] == 'OPERATIONAL'

        audit_res = httpx.get(f'http://127.0.0.1:{port}/api/audit/logs')
        assert audit_res.status_code == 200
        assert audit_res.json()['total'] >= 2

        qds_verify_res = httpx.post(f'http://127.0.0.1:{port}/api/qds/verify')
        assert qds_verify_res.status_code == 200
        assert 'classification' in qds_verify_res.json()

        forgery_res = httpx.post(f'http://127.0.0.1:{port}/api/attacks/simulate/forgery')
        assert forgery_res.status_code == 200
        assert forgery_res.json()['classification']['action'] == 'BLOCK'

        scenarios_res = httpx.get(f'http://127.0.0.1:{port}/scenarios')
        assert scenarios_res.status_code == 200
        assert len(scenarios_res.json()) == 3

        sim_scen_res = httpx.post(f'http://127.0.0.1:{port}/scenarios/simulate?scenario_id=healthcare_organ_dispatch')
        assert sim_scen_res.status_code == 200
        assert 'impact_summary' in sim_scen_res.json()
    finally:
        server.should_exit=True;thread.join(5);sock.close()
