/**
 * 案例库浏览页面 — 按诈骗类型筛选、搜索查看案例详情
 */
import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

const FRAUD_TYPES = [
  '全部', '刷单返利', '游戏交易', '虚假客服', '冒充老师',
  '虚假招聘', 'AI换脸', '求职培训贷', '网购退款', '虚假投资理财',
];

const MOCK_CASES = [
  { id: 1, type: '刷单返利', title: '大学生刷单被骗 2万元', summary: '受害人收到"兼职刷单"邀请，自称每单返利30%，前两单正常返利后投入大额本金被骗。', riskLevel: '高', evidence: ['刷单聊天记录', '转账凭证', '对方QQ号'], date: '2024-03-15' },
  { id: 2, type: '游戏交易', title: '游戏装备交易被钓鱼网站盗号', summary: '在某宝APP看到低价游戏装备，点击链接跳转到仿冒钓鱼网站，输入账号密码后被盗。', riskLevel: '中', evidence: ['钓鱼网站截图', '转账记录', '游戏账号被盗记录'], date: '2024-03-20' },
  { id: 3, type: '虚假客服', title: '假冒京东客服取消会员', summary: '接到自称京东客服电话，称误开了白金会员需取消，引导下载远程控制APP后转账。', riskLevel: '高', evidence: ['通话记录', 'APP下载记录', '银行卡扣款记录'], date: '2024-04-01' },
  { id: 4, type: '冒充老师', title: '班级群冒充老师收教材费', summary: '骗子潜入班级QQ群，将头像昵称改成班主任，发布假通知收取教材费。', riskLevel: '中', evidence: ['群聊截图', '收款二维码', '假通知原文'], date: '2024-04-10' },
  { id: 5, type: 'AI换脸', title: 'AI换脸视频冒充好友借钱', summary: '受害人收到"好友"视频电话，画面中的脸被AI替换，声称急需用钱请求转账。', riskLevel: '高', evidence: ['视频截图', '通话记录', '转账凭证'], date: '2024-05-01' },
  { id: 6, type: '求职培训贷', title: '招聘平台培训贷骗局', summary: '在招聘网站投简历后，收到面试通知，以"培训费"为名要求贷款，公司随后失联。', riskLevel: '高', evidence: ['招聘JD', '培训协议', '贷款合同'], date: '2024-05-15' },
  { id: 7, type: '网购退款', title: '假客服退款要求屏幕共享', summary: '收到自称淘宝客服的电话，称商品有质量问题需退款，引导开启屏幕共享并获取验证码。', riskLevel: '中', evidence: ['通话记录', '屏幕共享截图', '银行卡扣款记录'], date: '2024-06-01' },
  { id: 8, type: '虚假投资理财', title: '虚假数字货币投资平台', summary: '通过微信群接触"高回报"数字货币投资，先小赚后投入大额资金，平台随后无法登录。', riskLevel: '高', evidence: ['投资APP截图', '微信群聊天', '转账记录'], date: '2024-06-15' },
];

export default function CaseLibraryPage() {
  const [selectedType, setSelectedType] = useState('全部');
  const [search, setSearch] = useState('');
  const [selectedCase, setSelectedCase] = useState<typeof MOCK_CASES[0] | null>(null);
  const navigate = useNavigate();

  const filtered = useMemo(() => {
    return MOCK_CASES.filter((c) => {
      if (selectedType !== '全部' && c.type !== selectedType) return false;
      if (search && !c.title.includes(search) && !c.summary.includes(search)) return false;
      return true;
    });
  }, [selectedType, search]);

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 space-y-4">
      {/* 返回和标题 */}
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/knowledge')} className="text-gray-400 hover:text-gray-600 text-lg">&larr;</button>
        <h1 className="text-2xl font-bold text-gray-800">案例库</h1>
        <span className="text-sm text-gray-400">共计 {MOCK_CASES.length} 个案例</span>
      </div>

      {/* 搜索栏 */}
      <div className="relative">
        <input
          type="text"
          placeholder="搜索案例标题或内容..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-xl border border-gray-200 bg-white px-4 py-3 pl-10 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">🔍</span>
      </div>

      {/* 类型筛选 */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {FRAUD_TYPES.map((type) => (
          <button
            key={type}
            onClick={() => setSelectedType(type)}
            className={`shrink-0 px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
              selectedType === type
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {type}
          </button>
        ))}
      </div>

      {/* 案例列表 */}
      <div className="space-y-3">
        {filtered.map((c) => (
          <div
            key={c.id}
            onClick={() => setSelectedCase(selectedCase?.id === c.id ? null : c)}
            className="bg-white rounded-2xl p-4 border border-gray-100 shadow-sm cursor-pointer hover:shadow-md transition-shadow"
          >
            <div className="flex items-start gap-3">
              <div className={`shrink-0 w-10 h-10 rounded-xl flex items-center justify-center text-lg ${
                c.riskLevel === '高' ? 'bg-red-100' : c.riskLevel === '中' ? 'bg-amber-100' : 'bg-green-100'
              }`}>
                {c.riskLevel === '高' ? '⚠️' : c.riskLevel === '中' ? '⚡' : 'ℹ️'}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    c.riskLevel === '高' ? 'bg-red-50 text-red-600' : c.riskLevel === '中' ? 'bg-amber-50 text-amber-600' : 'bg-green-50 text-green-600'
                  }`}>
                    {c.riskLevel}风险
                  </span>
                  <span className="text-xs text-gray-400 bg-gray-50 px-2 py-0.5 rounded-full">{c.type}</span>
                  <span className="text-xs text-gray-400 ml-auto">{c.date}</span>
                </div>
                <h3 className="font-bold text-gray-800">{c.title}</h3>
              </div>
            </div>

            {/* 展开详情 */}
            {selectedCase?.id === c.id && (
              <div className="mt-3 pt-3 border-t border-gray-100">
                <div className="flex flex-wrap gap-2">
                  {c.evidence.map((e, i) => (
                    <span key={i} className="text-xs bg-blue-50 text-blue-600 px-2 py-1 rounded-lg">
                      📎 {e}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
