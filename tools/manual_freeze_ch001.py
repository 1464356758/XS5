"""One-time, user-authorized manual freeze through the existing V4.3 validators."""
import sys, json, subprocess
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import novel_state as ns
import narrative_quality as nq
import serial_release as sr
import online_state as oi

BOOK='5afdc2a3-0b3a-4e45-bbd0-f458aff8f3c3'
DRAFT=Path('drafts/CH001_未审全文.txt')

def verify(cond, msg):
    if not cond: raise ValueError(msg)

def main():
    request=ns.read_json('.automation/manual_freeze_CH001.json')
    verify(request == {'schema_version':1,'book_id':BOOK,'chapter':1,'draft_blob_sha':'75074ef6c0540fadda933d6a41dfae4dd42105c7','author_instruction':'开始第一章；按系统审核后正式冻结'},'作者授权或请求内容不匹配')
    verify(subprocess.check_output(['git','hash-object',str(DRAFT)],text=True).strip()==request['draft_blob_sha'],'草稿不同于已审版本')
    root=Path('book'); state=ns.load_state(root); ns.verify_files(root,state)
    verify(state['book_id']==BOOK and state['revision']==3 and not state['chapters'] and not state['tasks'],'章节或正式进度已经变化')
    verify(ns.read_json('.automation/config.json').get('automation_id') is None,'已有自动任务控制人，不可夺取执行权')
    body=DRAFT.read_text(encoding='utf-8'); sha=ns.digest(body)
    verify(ns.han_count(body)==9462 and not nq.surface_scan(body),'正文数值或制作痕迹异常')
    quote=lambda q: {'chapter':1,'sha256':sha,'quote':q}
    citations=['明天那场，我不唱了。','我先把明晚的走位停下来。','我没有学过这个。','不能用另一件东西假装他们买的就是这件。','七十一张，已收票款四千九百三十元。','账面可动三万二千四百。这四千九百三十包含在里面','我只想知道，戏院是不是以后都没有戏了。','月景停用待检查。勿擅自吊挂。','这一次，没有人把她拦住。','请勿按原场次到场。','一个月。','明天，先把票退。','合同该怎么算，您让田也按原来约定核。','内部练习不等于明晚能拿来放给买票的人。','我不能替她说原因。','你是不是站她那边？','我也知道它不能把我的后半辈子都唱进去。','《长街月》原安排暂停。','下次若有短一点的戏，别太晚散。']
    verify(all(q in body for q in citations),'实读引文不匹配正文，拒绝冻结')
    api=ns.serial_api(); brief=nq.brief_skeleton(state,api)
    brief.update(decision='ready',writer_brief='4月18日演员姜未央在次日晚告别演前辞演。许照作为舞台监督停止强行排练，陈小满试唱失败；团队核实旧票务、节目版权、安全装置与岗位边界，当晚公开停演，经营者给一个月有限的新短戏试验。所有行动由有权者做，预售票未实际退款时不能记已退。',hard_boundaries=['2026年4月18日辞演，4月19日19:30原定演出尚未发生。','71张预售4930元含于账面32400元，旧应付款约12000元，固定成本约26800元/月，不虚计还款。','姜未央原因未知，许照不得越权签合同，新人不能一夜学成主角。','未授权录音不得售票演出，旧月景停止使用待专业检验，156图纸席位不等于可售席位。'],reader_promise='开篇立即辞演，前三千字出现舞台与新人试唱失败，观众亲眼接触节目无法履约的后果；当晚发实际公告但不伪造已退款。',history_queries=[],scene_plan=[{'purpose':p,'target_han':c} for p,c in [('姜未央当面辞演与职业自主',1700),('试唱失败、女主停排及师生冲突',1600),('票款责任与乔奶奶现场问戏',1900),('技术停用、演员合法离场',1700),('停演通知、一个月有限试验与空台结尾',2400)]])
    ns.atomic_json('drafts/CH001_写作任务书.json',brief)
    nq.check_brief(root,Path('drafts/CH001_写作任务书.json'),api)
    Path('drafts/CH001_writer_context.txt').write_text(ns.context(root,profile='writer'),encoding='utf-8')
    ns.candidate(root,1,DRAFT)
    Path('drafts/CH001_reader_context.txt').write_text(ns.context(root,profile='reader',text_path=DRAFT),encoding='utf-8')
    facts=[('fact','show:Apr19:cancelled','姜未央退出，原定次日《长街月》无法按原阵容履约，实际退改尚未完成',0),('state','ticket:71:4930','71张预售票对应4930元退款或履约义务，不能冒充已退',4),('state','money:opening','账面32400元含4930元责任，旧应付12000元左右，月度基本成本估26800元',5),('fact','stage:moon:stopped','旧月景已停用待专业检查，不可用于明晚升降',7),('state','Jiang:exit','姜未央已递交退出说明，自愿离场，合同责任待核',8),('knowledge','Jiang:private_cause','许照不知姜未央具体私人原因，不能代她公开医疗详情',14),('state','ticket:notice','停售遗留渠道并发布停演告知，仍无凭据称退款到账',9),('state','trial:one-month','经营者限一个月试行新短戏，尚无完整原创剧本与售票场',10),('knowledge','Qiao:audience-needs','乔奶奶关心新戏是否较短以及散场时间，不代表同意改签',18)]
    record={'chapter':1,'title':'她说今晚不唱了','stage':'S01','base_revision':state['revision'],'canon_sha256':state['inputs']['canon']['sha256'],'text_sha256':sha,'complete':True,'story_time_end':1,'summary':'2026年4月18日，青灯戏院原定次日晚的告别场主演姜未央辞演。许照暂停排练，陈小满试唱失败。闻秋棠正式签收退出说明，具体责任待核；田也确认71票4930元仍有退改责任，账面32400元含该款，旧应付约12000元。乔奶奶到访关心未来演出，旧月景停用；戏院当晚停售遗留票并通知原场不能履约，但并未实际完成退款。闻秋棠给许照一个月的有限新戏试验，先处理旧票。','review':{'read_full_text':True,'decision':'adopt','blocking_issues':[],'sources_checked':[],'conclusion':'已读本章9462字全文和新书canon／roadmap；每次停演、人员离开、票款义务和权限均保留可核后果。人工审读为same_context_approximation，不冒充独立读者。第二章必须真正处理一批退款或经本人同意的改签，不能重复议事。'},'facts':[{'kind':kind,'key':key,'value':value,'holder':'许照' if kind=='knowledge' else '','valid_from':1,'valid_until':None,'quote':citations[idx]} for kind,key,value,idx in facts], 'progression':{'goal':'完成原定告别场并对观众负责','obstacle':'主演辞演、新人不能替演、权责和经费不足','method':'停止原排练，核实票务和实物，在有权经营者确认后停售并如实公告','choice':'不强迫姜未央，不拿未授权录音蒙混，不让不具备能力的新人硬唱；先退改旧票再制作新戏','result':'原演出确定不按原阵容举行，公告已发，新戏试验获一个月条件性许可','consequence':'71张票对应钱与信任仍待处理，观众失望，月景停用，演员离场','next_options':'CH002逐票核实际退票或本人确认的改签；CH003开始可实现的原创小段','scene_function':'辞演钩、试唱失败、观众反馈、道具停用、公开通知、试验约束与退票悬念'},'thread_events':[{'id':k,'action':'plant','description':d,'quote':citations[i]} for k,d,i in [('P01-original-show','原演出无法按原阵容履约，实际退改需下一章兑现',9),('P02-ticket-refunds','71张票4930元仍须处理，不能只通知不退款',11),('P03-new-short-show','一个月的合法原创新短场最迟第十章交付',10),('P04-Jiang-exit','姜未央合同责任及未解释的原因须在第七章前交代',12),('P05-content-rights','原剧录音与原创文本和音乐版权需第四章前核清',13)]],'stage_closing':False}
    recpath=Path('drafts/CH001_章后事实记录.json');ns.atomic_json(recpath,record)
    ns.validate_record(root,ns.load_state(root),body,record)
    report=sr.skeleton(root,ns.load_state(root),body,record,api)
    report.update(decision='release',read_full_text=True,blocking_issues=[],reader_reason_to_continue='71张票与4930元尚未实际退改，第二章须从真实观众和渠道回款推进，不停在通知。',consequence='原节目正式不可如期，姜未央离开，舞美停用，观众面临退改；一个月试演尚无本子和保证。',ending_runway='100章长篇刚开始，第一卷第十章必须有一场真正完成的合法付费原创短戏。')
    decisions=[('timeline','事件按4月18日下午至当晚顺序推进；4月19日未被虚写为成功演出',0),('knowledge','个人退出原因未知，角色不凭空掌握姜未央私人细节',14),('props_resources','4930元包含在32400元现金，不重复计算；旧款未清，月景停用',5),('causality','辞演令试唱失败、停演、停售、告知和有限新戏试验依次发生',2),('power_rules','许照不冒充有权经营者，旧录音与舞美未核的使用受到限制',13),('promises','原场停演已兑现，票款退改留第2章实做，试演留第10章',11),('anti_repeat','本书无前文冻结章；本章有试唱、搬景和真人到访，并非只讨论合同',7),('character_agency','许照自己停排并选择不逼唱；闻秋棠确认条件而非无条件给钱',1)]
    report['checks']={k:{'decision':'pass','conclusion':d,'evidence':[quote(citations[i])]} for k,d,i in decisions}
    report['comparison']=[]
    report['future_window']=[{'chapter':n,'goal':g,'change':c,'ending_question':e} for n,g,c,e in [(2,'逐票处理原71张售票','至少一部分真实退票或获得本人改签同意','仍未联系者与远道观众如何处理'),(3,'验证不需要旧头牌的舞台形式','舍弃强行顶角方案并启动原创小戏','旧本子授权与音乐如何取得'),(4,'区分旧戏与新戏的使用权','取得有限新剧本和音乐授权','是否能排出可交给观众的短场')]]
    report['opening']={k:{'quote':citations[i],'why':why} for k,i,why in [('first_hook',0,'开场立刻宣告明晚主角辞演'),('core_promise',17,'前期直接暂停不能如期排演的戏院场景'),('protagonist_impact',1,'女主立即选择停排并承受与经营者的冲突')]}
    deadlines={'P01-original-show':2,'P02-ticket-refunds':2,'P03-new-short-show':10,'P04-Jiang-exit':7,'P05-content-rights':4}
    for x in report['promise_reviews']:
        x.update(action='set',deadline_chapter=deadlines[x['id']],reason='本章已种下义务但实际行动未全部完成；按前五章和首卷路线设到期限制。',evidence=quote(citations[11 if x['id']=='P02-ticket-refunds' else 10 if x['id']=='P03-new-short-show' else 13 if x['id']=='P05-content-rights' else 12 if x['id']=='P04-Jiang-exit' else 9]))
    nar=report['narrative_review']
    actions=[('辞演当面告知','姜未央要求退出','原主演明晚不演',0),('新人试唱失败','许照停止逼新人替演','原剧无法蒙混',2),('师生冲突','许照坚持观众有权知情','经营者必须面对责任',3),('田也核对预售','团队停售并区分预售与可用资金','71票4930元仍是负债',4),('真实老观众来询问','许照拒绝虚假再开保证','观众需求具体化',6),('月景从台上搬离','曹文修与许照选择停用','技术方案缩减',7),('姜未央实际离场','闻秋棠签收说明','退出不被情分拦住',8),('公告正式发布','田也给观众退改选择','未退款但完成告知',9),('经营者提出一个月','许照接受预算约束','有限新戏试验而非无条件复开',10),('空台写明先退票','许照优先处理退款实际责任','下一章有明确兑现',11)]
    nar['actual_scenes']=[{'event':a,'choice':c,'change':d,'evidence':[quote(citations[i])]} for a,c,d,i in actions]
    nar['plan_comparison']='预定的五大段实际拆成十个场景：辞演、试唱失败、师生冲突、现金核算、老观众、停用装置、员工离场、公开告知、有条件试验、收灯结尾。退改尚未完成，必须于下一章真做。'
    nar['reader'].update(mode='same_context_approximation',limitation='同一模型曾参与写作与审读，不是独立读者或真实咪咕编辑。',understanding='主角不是全能歌者或经营者，头牌退出后旧戏无法照演，读者能跟随人物看到真实戏院和观众的处境。',information_load='票款与欠款数额相对集中，但穿插真实老人到访、灯景搬动，第二章不宜再次仅会议解释。',promise_delivery='首章如实通知原戏无法交付；正式退款、原创剧本与合法售票场仍未发生。',evidence=[quote(citations[0]),quote(citations[11])],issues=[{'severity':'suggestion','status':'open','reason':'票务段落解释稍多，但不阻断理解；第二章需大量实际观众行动和退款回执。','evidence':quote(citations[4])}])
    nar['character_causality']={name:{'status':'reviewed','conclusion':desc,'evidence':[quote(citations[i])]} for name,desc,i in [('opposition','闻秋棠不愿失去十年告别戏却最终签收退出，有职业权责而不是简单反派',15),('dialogue','姜未央守住自由，闻秋棠维护情感，田也考虑票款，声音和诉求不同',16),('aftermath','演员离开、停演通知和月景停用都是真实不可逆变化',8)]}
    nar['history'].update(queries=[],comparisons=[],no_match_reason='这是新书第一章，当前仓库正式冻结前文为0章；无同书前章可比，后续须全文回读本章。')
    nar['reader_updates']=[{'kind':kind,'statement':desc,'evidence':[quote(citations[i])]} for kind,desc,i in [('observed','原主演宣布辞演，次日晚旧戏无法按原阵容交付',0),('observed','已售71票4930元仍需退改',4),('observed','旧月景停用待检，团队不能冒险上台',7),('claim','闻秋棠给一个月有限时间试验新短戏',10),('uncertain','姜未央的实际私人原因未向女主证实',14)]]
    nar['reader_update_note']='首章揭示的仅是原戏停演、真实售票义务与有限试验，没写旧责任已了或新戏已成。'
    verify(not nar['surface_findings'],'正文仍有制作语言需人工判定')
    reportfile=Path('drafts/CH001_发布前实审报告.json');ns.atomic_json(reportfile,report)
    sr.check(root,DRAFT,recpath,reportfile,api)
    ns.adopt(root,DRAFT,recpath)
    wf=oi.load_workflow('.');verify(wf['book_id']==BOOK and wf['chapter']==1,'工作流目标已改变')
    wf['chapter']=2;oi.write_workflow('.',wf,phase='WAITING_NEXT',detail='CH001《她说今晚不唱了》通过原V4.3审读和release-check，已采用冻结；未登记咪咕平台发布。',next_action='继续CH002《七十一张票》，实际办理首批合法退改并留存未结责任。')
    oi.build_index('.');oi.validate_index('.')
    final=ns.load_state(root)
    verify(str(1) in final['serialization']['frozen'] and final['serialization']['gates']['1']['used'] is True,'正式冻结未成立')
    verify(final['chapters']['1']['text_sha256']==sha and not final['serialization']['published'],'正文哈希或平台登记异常')
    print(json.dumps({'status':'LOCKED','chapter':1,'han':ns.han_count(body),'chapter_path':final['chapters']['1']['text_path'],'record_path':final['chapters']['1']['record_path'],'release_path':final['serialization']['gates']['1']['path'],'sha256':sha,'adopted_at':final['chapters']['1']['adopted_at']},ensure_ascii=False))

if __name__=='__main__':main()
