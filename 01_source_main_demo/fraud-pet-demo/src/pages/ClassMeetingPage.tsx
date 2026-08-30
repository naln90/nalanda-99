/**
 * 班会素材生成 — 基于班级薄弱维度生成讨论话题与活动建议
 */
import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { getDimensionColor } from '../lib/constants';

interface WeakDimension {
  dimension: string;
  count: number;
}

interface ClassMeetingTopic {
  dimension: string;
  weakCount: number;
  topic: string;
  questions: string[];
  activity: string;
}

interface ClassMeetingData {
  generatedAt: string;
  classProfile: { totalAssessed: number; topWeakDimensions: WeakDimension[] };
  topics: ClassMeetingTopic[];
  suggestions: string[];
}

export default function ClassMeetingPage() {
  const navigate = useNavigate();
  const [data, setData] = useState<ClassMeetingData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    api
      .getClassMeetingMaterials()
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : '班会素材加载失败，请稍后重试'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return <div className="flex items-center justify-center py-20 text-muted-foreground">生成班会素材中...</div>;
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-10 text-center space-y-4">
        <p className="text-gray-600">班会素材加载失败：{error}</p>
        <button onClick={load} className="mx-auto block bg-blue-500 text-white px-6 py-2 rounded-lg">
          重试
        </button>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-10">
        <button onClick={() => navigate('/counselor/dashboard')} className="mt-4 mx-auto block bg-blue-500 text-white px-6 py-2 rounded-lg">
          返回看板
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
      {/* 标题 */}
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold text-gray-800">班会素材</h1>
        <span className="text-sm text-gray-400">
          生成于 {new Date(data.generatedAt).toLocaleString('zh-CN')}
        </span>
      </div>

      {/* 班级概况 */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-2xl p-5 border border-blue-200">
        <h2 className="font-bold text-blue-800 mb-3">班级薄弱维度概况</h2>
        <p className="text-sm text-blue-600 mb-3">
          已测评学生: {data.classProfile.totalAssessed} 人
        </p>
        <div className="flex gap-3 flex-wrap">
          {data.classProfile.topWeakDimensions?.map((d) => (
            <div
              key={d.dimension}
              className="bg-white rounded-lg px-4 py-2 shadow-sm"
              style={{ borderColor: getDimensionColor(d.dimension), borderWidth: 2 }}
            >
              <p className="font-bold text-gray-800">{d.dimension}</p>
              <p className="text-sm text-gray-500">{d.count} 人薄弱</p>
            </div>
          ))}
        </div>
      </div>

      {/* 讨论话题 */}
      <div className="space-y-4">
        <h2 className="font-bold text-gray-800 text-lg">📝 讨论话题与活动</h2>
        {data.topics?.map((topic) => (
          <div
            key={topic.dimension}
            className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm"
          >
            <div className="flex items-center gap-2 mb-3">
              <span
                className="w-4 h-4 rounded-full"
                style={{ backgroundColor: getDimensionColor(topic.dimension) }}
              />
              <h3 className="font-bold text-gray-800">{topic.topic}</h3>
              <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">
                {topic.weakCount} 人薄弱 · {topic.dimension}
              </span>
            </div>
            <div className="space-y-3">
              <div>
                <ul className="space-y-1">
                  {topic.questions?.map((q: string, idx: number) => (
                    <li key={idx} className="text-sm text-gray-700 pl-4 relative before:content-['▸'] before:absolute before:left-0 before:text-amber-500">
                      {q}
                    </li>
                  ))}
                </ul>
              </div>
                <div className="bg-green-50 rounded-lg p-3 border border-green-200">
                  <p className="text-sm text-green-600">{topic.activity}</p>
                </div>
            </div>
          </div>
        ))}
      </div>

      {/* 辅导员建议 */}
      <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
        <h2 className="font-bold text-gray-800 text-lg mb-3">💡 辅导员建议</h2>
        <ul className="space-y-2">
          {data.suggestions?.map((s: string, idx: number) => (
            <li key={idx} className="text-sm text-gray-700 pl-4 relative before:content-['✓'] before:absolute before:left-0 before:text-green-500">
              {s}
            </li>
          ))}
        </ul>
      </div>

      {/* 返回按钮 */}
      <button
        onClick={() => navigate('/counselor/dashboard')}
        className="w-full bg-gray-100 text-gray-600 rounded-xl p-3 font-medium hover:bg-gray-200 transition-colors"
      >
        返回看板
      </button>
    </div>
  );
}
