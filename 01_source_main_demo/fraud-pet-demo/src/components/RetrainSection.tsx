/**
 * 复训提示卡片 — 展示到期的复训任务
 * 集成到 HomePage 或 TrainingPage 中
 */
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../store/useAppStore';
import { getDimensionColor } from '../lib/constants';

const VARIANT_LABELS: Record<string, string> = {
  change_options_order: '选项顺序变换',
  change_scenario_detail: '情景细节改编',
  change_question_type: '题型转换',
};

// 诈骗类型 → 场景路由参数映射
const FRAUD_TYPE_TO_SCENARIO: Record<string, string> = {
  '刷单返利': 'brush_orders',
  '游戏交易': 'game_trade',
  '虚假客服': 'fake_customer_service',
  '冒充老师': 'fake_teacher',
  '虚假招聘': 'fake_recruitment',
  '奖助学金': 'scholarship',
  'AI换脸': 'ai_face_swap',
  '求职培训贷': 'training_loan',
  '网购退款': 'refund',
  '虚假投资理财': 'investment',
};

export default function RetrainSection() {
  const dueRetrains = useAppStore((s) => s.dueRetrains);
  const loadDueRetrains = useAppStore((s) => s.loadDueRetrains);
  const navigate = useNavigate();

  useEffect(() => {
    loadDueRetrains();
  }, [loadDueRetrains]);

  if (dueRetrains.length === 0) return null;

  const handleRetrain = (rt: typeof dueRetrains[0]) => {
    if (rt.variantStrategy === 'change_scenario_detail' && rt.fraudType) {
      const scenarioKey = FRAUD_TYPE_TO_SCENARIO[rt.fraudType] ?? 'brush_orders';
      navigate(`/training/scenario/${scenarioKey}`);
    } else {
      navigate('/training');
    }
  };

  return (
    <div className="bg-gradient-to-r from-amber-50 to-orange-50 rounded-2xl p-4 border border-amber-200 shadow-sm">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-2xl">🔄</span>
        <h3 className="text-lg font-bold text-amber-800">复训提醒</h3>
        <span className="bg-amber-500 text-white text-xs px-2 py-0.5 rounded-full font-medium">
          {dueRetrains.length} 项待完成
        </span>
      </div>
      <div className="space-y-2">
        {dueRetrains.slice(0, 3).map((rt) => (
          <div
            key={rt.id}
            className="flex items-center gap-3 bg-white/70 rounded-lg p-3 cursor-pointer hover:bg-white transition-colors"
            onClick={() => handleRetrain(rt)}
          >
            <div
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: getDimensionColor(rt.targetAbility ?? '') }}
            />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-800 truncate">
                {rt.fraudType ?? '综合'} · 第 {rt.attempt ?? 1} 次复训
              </p>
              <p className="text-xs text-gray-500">
                变体策略: {VARIANT_LABELS[rt.variantStrategy] || rt.variantStrategy}
              </p>
            </div>
            <span className="text-xs text-amber-600 whitespace-nowrap">
              {new Date(rt.scheduledAt).toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })}
            </span>
          </div>
        ))}
      </div>
      {dueRetrains.length > 3 && (
        <p className="text-xs text-amber-600 mt-2 text-center">
          还有 {dueRetrains.length - 3} 项待完成...
        </p>
      )}
    </div>
  );
}
