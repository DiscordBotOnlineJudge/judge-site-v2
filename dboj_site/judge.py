import grpc
import dboj_site.judge_pb2_grpc
import dboj_site.judge_pb2

def runSubmission(judges, username, cleaned, lang, problm, attachments, return_dict):
    with grpc.insecure_channel(judges['ip'] + ":" + str(judges['port'])) as channel:
        stub = judge_pb2_grpc.JudgeServiceStub(channel)
        response = stub.judge(judge_pb2.SubmissionRequest(username = username, source = cleaned, lang = lang, problem = problm['name'], attachment = attachments))
        finalscore = response.finalScore
        return_dict['finalscore'] = finalscore