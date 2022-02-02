import grpc
import dboj_site.judge_pb2_grpc as judge_pb2_grpc
import dboj_site.judge_pb2 as judge_pb2

def runSubmission(judges, username, cleaned, lang, problm, attachments, return_dict, sub_id):
    with grpc.insecure_channel(judges['ip'] + ":" + str(judges['port'])) as channel:
        stub = judge_pb2_grpc.JudgeServiceStub(channel)
        response = stub.judge(judge_pb2.SubmissionRequest(username = username, source = cleaned, lang = lang, problem = problm, attachment = attachments, sub_id = sub_id))
