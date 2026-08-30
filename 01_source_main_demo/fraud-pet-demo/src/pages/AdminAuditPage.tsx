/**
 * 人工审核入库页面 — 管理员审核用户提交的内容
 * 展示待审核列表，支持通过/驳回操作
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface AuditItem {
  id: string;
  type: 'training_data' | 'case_report' | 'knowledge_entry';
  typeLabel: string;
  submittedBy: string;
  submittedAt: string;
  title: string;
  content: string;
  status: 'pending' | 'approved' | 'rejected';
}

const MOCK_ITEMS: AuditItem[] = [
  {
    id: 'AUD-001',
    type: 'training_data',
    typeLabel: '训练数据',
    submittedBy: 'U-2408**',
    submittedAt: '2024-06-15 14:30',
    title: '新增「刷单返利」情景训练题目',
    content: '题目: "在刷单诈骗中，骗子通常会用什么话术来降低受害者的警惕性？" 选项: A. "先试一单看看" B. "这个是正规兼职" C. "已经有很多人在做了" D. 以上都是',
    status: 'pending',
  },
  {
    id: 'AUD-002',
    type: 'case_report',
    typeLabel: '案例报告',
    submittedBy: 'U-2407**',
    submittedAt: '2024-06-14 09:15',
    title: '校园AI换脸诈骗案例提交',
    content: '案例描述: 学生A在视频通话中被"好友"借走5000元，后确认对方使用了AI换脸技术。包含视频截图、转账记录、聊天记录等证据。',
    status: 'pending',
  },
  {
    id: 'AUD-003',
    type: 'knowledge_entry',
    typeLabel: '知识词条',
    submittedBy: 'U-2409**',
    submittedAt: '2024-06-13 16:45',
    title: '「求职培训贷」知识库新增',
    content: '新增知识条目: 求职培训贷的特征包括——1.以招聘为名要求培训 2.要求签订培训贷款协议 3.培训内容与岗位无关 4.公司无实际业务。',
    status: 'pending',
  },
];

const TYPE_ICONS: Record<string, string> = {
  training_data: '📝',
  case_report: '📄',
  knowledge_entry: '📚',
};

export default function AdminAuditPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState<AuditItem[]>(MOCK_ITEMS);
  const [filter, setFilter] = useState<'all' | 'pending' | 'approved' | 'rejected'>('pending');

  const filtered = items.filter((i) => filter === 'all' || i.status === filter);

  const handleAction = (id: string, action: 'approved' | 'rejected') => {
    setItems(items.map((i) => i.id === id ? { ...i, status: action } : i));
  };

  const pendingCount = items.filter((i) => i.status === 'pending').length;
  const approvedCount = items.filter((i) => i.status === 'approved').length;
  const rejectedCount = items.filter((i) => i.status === 'rejected').length;

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 space-y-4">
      {/* 标题 */}
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/home')} className="text-gray-400 hover:text-gray-600 text-lg">&larr;</button>
        <h1 className="text-2xl font-bold text-gray-800">人工审核</h1>
        <span className="bg-red-500 text-white text-xs px-2 py-0.5 rounded-full font-medium">
          {pendingCount} 待审
        </span>
      </div>

      {/* 统计概览 */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-amber-50 rounded-xl p-3 text-center border border-amber-200">
          <p className="text-2xl font-bold text-amber-600">{pendingCount}</p>
          <p className="text-xs text-amber-600">待审核</p>
        </div>
        <div className="bg-green-50 rounded-xl p-3 text-center border border-green-200">
          <p className="text-2xl font-bold text-green-600">{approvedCount}</p>
          <p className="text-xs text-green-600">已通过</p>
        </div>
        <div className="bg-red-50 rounded-xl p-3 text-center border border-red-200">
          <p className="text-2xl font-bold text-red-600">{rejectedCount}</p>
          <p className="text-xs text-red-600">已驳回</p>
        </div>
      </div>

      {/* 筛选标签 */}
      <div className="flex gap-2">
        {([
          { key: 'pending', label: '待审核' },
          { key: 'approved', label: '已通过' },
          { key: 'rejected', label: '已驳回' },
          { key: 'all', label: '全部' },
        ] as const).map((t) => (
          <button
            key={t.key}
            onClick={() => setFilter(t.key)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
              filter === t.key ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* 审核列表 */}
      <div className="space-y-3">
        {filtered.map((item) => (
          <div key={item.id} className="bg-white rounded-2xl p-4 border border-gray-100 shadow-sm">
            <div className="flex items-start gap-3 mb-3">
              <div className="shrink-0 w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center text-lg">
                {TYPE_ICONS[item.type] || '📋'}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs bg-gray-50 text-gray-500 px-2 py-0.5 rounded-full">{item.typeLabel}</span>
                  <span className="text-xs text-gray-400">{item.submittedBy}</span>
                  <span className="text-xs text-gray-400 ml-auto">{item.submittedAt}</span>
                </div>
                <h3 className="font-bold text-gray-800">{item.title}</h3>
                <p className="text-sm text-gray-500 mt-1 line-clamp-2">{item.content}</p>
              </div>
            </div>

            {/* 审核操作按钮 */}
            {item.status === 'pending' ? (
              <div className="flex gap-2 pt-3 border-t border-gray-50">
                <button
                  onClick={() => handleAction(item.id, 'approved')}
                  className="flex-1 bg-green-500 text-white rounded-lg py-2 text-sm font-medium hover:bg-green-600 transition-colors"
                >
                  ✓ 通过入库
                </button>
                <button
                  onClick={() => handleAction(item.id, 'rejected')}
                  className="flex-1 bg-red-500 text-white rounded-lg py-2 text-sm font-medium hover:bg-red-600 transition-colors"
                >
                  ✗ 驳回
                </button>
                <button
                  className="px-4 bg-gray-100 text-gray-600 rounded-lg py-2 text-sm font-medium hover:bg-gray-200 transition-colors"
                >
                  查看详情
                </button>
              </div>
            ) : (
              <div className="pt-3 border-t border-gray-50 flex items-center gap-2">
                <span className={`text-sm font-medium ${
                  item.status === 'approved' ? 'text-green-600' : 'text-red-600'
                }`}>
                  {item.status === 'approved' ? '✓ 已通过' : '✗ 已驳回'}
                </span>
                <button
                  onClick={() => handleAction(item.id, item.status === 'approved' ? 'rejected' : 'approved')}
                  className="text-xs text-blue-500 hover:text-blue-600 ml-auto"
                >
                  撤回
                </button>
              </div>
            )}
          </div>
        ))}
        {filtered.length === 0 && (
          <p className="text-center text-gray-400 py-10">暂无{filter === 'all' ? '' : filter === 'pending' ? '待审核' : filter === 'approved' ? '已通过' : '已驳回'}的项目</p>
        )}
      </div>
    </div>
  );
}
