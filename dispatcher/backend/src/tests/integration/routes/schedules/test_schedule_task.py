import json

import pytest

"""
Test interaction with `offliner` property of schedule. 
The `offliner` property is an object, containing:
  - offliner name to use
  - offliner configuration
"""


# class TestScheduleTaskConfigGet:
#     def test_offliner_mwoffliner(self, client, access_token, schedule):
#         """Test get task config"""
#
#         schedule_id = schedule['_id']
#         url = '/api/schedules/{schedule}/task'.format(schedule=str(schedule_id))
#         response = client.get(url, headers={'Authorization': access_token})
#         assert response.status_code == 200
#         assert schedule['task'] == response.get_json()
#
#         schedule_name = schedule['name']
#         url = '/api/schedules/{schedule}/task'.format(schedule=str(schedule_name))
#         response = client.get(url, headers={'Authorization': access_token})
#         assert response.status_code == 200
#         assert schedule['task'] == response.get_json()
#
#     def test_no_access_token(self, client, schedule):
#         """Test cannot get offliner without access token"""
#
#         url = '/api/schedules/{schedule}/task'.format(schedule=str(schedule['_id']))
#         response = client.get(url)
#         assert response.status_code == 401
#
#     def test_bad_schedule_id_or_name(self, client, access_token, schedule):
#         """Test cannot get offliner with a bad schedule id or name"""
#
#         url = '/api/schedules/{schedule}/task'.format(schedule='bad_schedule_id')
#         response = client.get(url, headers={'Authorization': access_token})
#         assert response.status_code == 404


# class TestScheduleTaskConfigMWOfflinerUpdate:
#     def test_update_full(self, client, access_token, make_task_mwoffliner, make_schedule):
#         """Test update offliner with new mwoffliner config"""
#
#         schedule = make_schedule('name', 'language', 'wikipedia')
#         url = '/api/schedules/{schedule}/offliner'.format(schedule=str(schedule['_id']))
#         offliner = make_task_mwoffliner(sub_domain='bm', admin_email='admin@example.com')
#
#         # update beat
#         headers = {'Authorization': access_token, 'Content-Type': 'application/json'}
#         response = client.patch(url, headers=headers, data=json.dumps(offliner))
#         assert response.status_code == 200
#
#         # check updated value
#         response = client.get(url, headers={'Authorization': access_token})
#         assert response.status_code == 200
#         assert offliner == response.get_json()
#
#     @pytest.mark.parametrize('body', [
#         None, '', 'bad_body', '{"name": "bad_name", "config": {}}', '{"name": "bad_name", "config": null}'
#     ])
#     def test_bad_body(self, client, access_token, schedule, body):
#         """Test cannot update offliner with a bad request body"""
#
#         url = '/api/schedules/{schedule}/offliner'.format(schedule=str(schedule['_id']))
#         headers = {'Authorization': access_token, 'Content-Type': 'application/json'}
#         response = client.patch(url, headers=headers, data=body)
#         assert response.status_code == 400
#
#     @pytest.mark.parametrize('config', [
#         {'mwURL': 'https://en.wikipedia.org/', 'adminEmail': 'admin@kiwix.org'},
#         {'mwUrl': 'htts:/en.wikipedia.org/', 'adminEmail': 'admin@kiwix.org'},
#         {'mwUrl': 'https://en.wikipedia.org/', 'adminEmail': 'adminkiwix.org'}
#     ])
#     def test_bad_config(self, client, access_token, schedule, config):
#         """Test cannot update offliner with a bad request body"""
#
#         url = '/api/schedules/{schedule}/offliner'.format(schedule=str(schedule['_id']))
#         headers = {'Authorization': access_token, 'Content-Type': 'application/json'}
#         response = client.patch(url, headers=headers, data=json.dumps({'name': 'mwoffliner', 'config': config}))
#         assert response.status_code == 400
#
#     def test_bad_content_type(self, client, access_token, schedule, make_task_mwoffliner):
#         """Test cannot update offliner with a bad content type"""
#
#         offliner = make_task_mwoffliner(sub_domain='bm', admin_email='admin@example.com')
#         url = '/api/schedules/{schedule}/offliner'.format(schedule=str(schedule['_id']))
#         headers = {'Authorization': access_token}
#         response = client.patch(url, headers=headers, data=json.dumps(offliner))
#         assert response.status_code == 400
#
#     def test_patch_no_access_token(self, client, schedule, make_task_mwoffliner):
#         """Test cannot update offliner without access token"""
#
#         offliner = make_task_mwoffliner(sub_domain='bm', admin_email='admin@example.com')
#         url = '/api/schedules/{schedule}/offliner'.format(schedule=str(schedule['_id']))
#         headers = {'Content-Type': 'application/json'}
#         response = client.patch(url, headers=headers, data=json.dumps(offliner))
#         assert response.status_code == 401
#
#     def test_patch_bad_schedule_id_or_name(self, client, access_token, make_task_mwoffliner):
#         """Test cannot update offliner with a bad schedule id or name"""
#
#         offliner = make_task_mwoffliner(sub_domain='bm', admin_email='admin@example.com')
#         url = '/api/schedules/{schedule}/offliner'.format(schedule='bad_schedule_id')
#         headers = {'Authorization': access_token, 'Content-Type': 'application/json'}
#         response = client.patch(url, headers=headers, data=json.dumps(offliner))
#         assert response.status_code == 404
