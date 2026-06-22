# 基金评分字段中文映射（get_fund_score）

## 文档说明

- 本文档用于说明 `get_fund_score` 返回字段的中文含义。
- 不同 `score_type` 的返回字段不同，请按对应类型查看。
- 建议结合 `rankconfig_id.md` 中的 `score_type` 一起使用。

## mix(混合型)

```json
{
  "annualyield": "年化收益率",
  "drawback": "最大回撤",
  "sharpe": "夏普比率",
  "annualdownsd": "下行标准差",
  "daywinrate": "对比基准胜率",
  "assetallocation": "大类资产配置能力",
  "styleallocation": "风格配置能力",
  "industryallocation": "行业配置能力",
  "durationallocation": "期限配置能力",
  "creditallocation": "信用配置能力",
  "scene_doublekill": "股债双杀",
  "scene_stockup_bonddown": "股涨债跌",
  "scene_stockdown_bondup": "股跌债涨",
  "scene_stockup_bondup": "股债双牛",
  "scene_stockup_bondbumpy": "股涨债震",
  "scene_stockdown_bondbumpy": "股跌债震",
  "scene_marketdown_largecap": "市场下跌，大盘股>小盘股",
  "scene_marketdown_volatilityup": "市场下跌，波动率上升",
  "scene_marketup_smallcap": "市场上涨，大盘股<小盘股",
  "scene_marketup_volatilityup": "市场上涨，波动率上升",
  "scene_govbondup_durationup": "国债利率上升，期限利差上升",
  "scene_govbondup_durationdown": "国债利率上升，期限利差下跌",
  "scene_govbonddown_durationup": "国债利率下跌，期限利差上升",
  "scene_govbonddown_durationdown": "国债利率下跌，期限利差下跌",
  "alpha_asset_bond": "大类资产配置超额能力",
  "alpha_risk_stock": "风险因子超额能力(股票)",
  "alpha_style": "风格配置超额能力",
  "alpha_industry": "行业配置超额能力",
  "alpha_risk_bond": "风险因子超额能力(债券)",
  "alpha_duration": "期限配置超额能力",
  "alpha_credit": "信用配置超额能力",
  "performance": "绩效质量_三级",
  "asset_i": "一级资产配置能力",
  "asset_ii_stock": "二级资产配置能力(股票)",
  "asset_ii_bond": "二级资产配置能力(债券)",
  "scene_i": "一级场景应对能力",
  "scene_ii_stock": "二级场景应对能力(股票)",
  "scene_ii_bond": "二级场景应对能力(债券)",
  "alpha_i": "一级alpha获取能力",
  "alpha_ii_stock": "二级alpha获取能力(股票)",
  "alpha_ii_bond": "二级alpha获取能力(债券)",
  "performance_overall": "绩效质量",
  "asset_overall": "资产配置能力",
  "scene_overall": "场景应对能力",
  "alpha_overall": "alpha获取能力",
  "total": "总分"
}
```

## bond(债券型)

```json
{
  "annualyield": "年化收益率",
  "drawback": "最大回撤",
  "sharpe": "夏普比率",
  "annualdownsd": "下行标准差",
  "sortino": "索提诺比率",
  "assetallocation": "大类资产配置能力",
  "durationallocation": "期限配置能力",
  "creditallocation": "信用配置能力",
  "scene_govbondup_durationup": "国债利率上升，期限利差上升",
  "scene_govbondup_durationdown": "国债利率上升，期限利差下跌",
  "scene_govbonddown_durationup": "国债利率下跌，期限利差上升",
  "scene_govbonddown_durationdown": "国债利率下跌，期限利差下跌",
  "alpha_asset_bond": "大类资产配置超额能力",
  "alpha_risk_bond": "风险因子超额能力(债券)",
  "alpha_duration": "期限配置超额能力",
  "alpha_credit": "信用配置超额能力",
  "performance_overall": "绩效质量",
  "asset_overall": "资产配置能力",
  "scene_overall": "场景应对能力",
  "alpha_overall": "alpha获取能力",
  "total": "总分"
}
```

## long(股票型)

```json
{
  "annualyield": "年化收益率",
  "drawback": "最大回撤",
  "sharpe": "夏普比率",
  "annualdownsd": "下行标准差",
  "daywinrate": "对比基准胜率",
  "assetallocation": "大类资产配置能力",
  "styleallocation": "风格配置能力",
  "industryallocation": "行业配置能力",
  "scene_marketdown_largecap": "市场下跌，大盘股>小盘股",
  "scene_marketdown_volatilityup": "市场下跌，波动率上升",
  "scene_marketup_smallcap": "市场上涨，大盘股<小盘股",
  "scene_marketup_volatilityup": "市场上涨，波动率上升",
  "alpha_asset": "大类资产配置超额能力",
  "alpha_risk_stock": "风险因子超额能力(股票)",
  "alpha_style": "风格配置超额能力",
  "alpha_industry": "行业配置超额能力",
  "performance_overall": "绩效质量",
  "asset_overall": "资产配置能力",
  "scene_overall": "场景应对能力",
  "alpha_overall": "alpha获取能力",
  "total": "总分"
}
```

## neutral(市场中性型)

```json
{
  "annualyield": "年化收益率",
  "drawback": "最大回撤",
  "drawbackdays": "回撤回补最长周期",
  "sharpe": "夏普比率",
  "annualdownsd": "下行标准差",
  "daywinrate": "对比基准胜率",
  "styleallocation": "风格配置能力",
  "industryallocation": "行业配置能力",
  "scene_marketdown_largecap": "市场下跌，大盘股>小盘股",
  "scene_marketdown_volatilitydown": "市场下跌，波动率下降",
  "scene_marketdown_alphadown": "市场下跌，alpha机会下降",
  "scene_marketup_smallcap": "市场上涨，大盘股<小盘股",
  "scene_marketup_volatilityup": "市场上涨，波动率上升",
  "alpha_capacity": "alpha获取能力_三级",
  "performance_overall": "绩效质量",
  "asset_overall": "资产配置能力",
  "scene_overall": "场景应对能力",
  "alpha_overall": "alpha获取能力",
  "total": "总分"
}
```

## cta(CTA型)

```json
{
  "annualyield": "年化收益率_四级",
  "drawback": "最大回撤_四级",
  "calmar": "卡玛比率_四级",
  "annualdownsd": "下行标准差_四级",
  "monthwinrate": "对比基准胜率_四级",
  "alpha_style": "风格因子上的超额能力_四级",
  "allocation_race": "赛道因子上的配置能力_四级",
  "scene_040101": "高信噪比高波动率",
  "scene_040102": "高信噪比低波动率",
  "scene_040103": "低信噪比高波动率",
  "scene_040104": "低信噪比低波动率",
  "scene_040301": "股指风格差",
  "scene_040302": "指数下行",
  "scene_040303": "加息",
  "scene_040305": "商品市场震荡",
  "scene_040306": "股指波动大增",
  "scene_040309": "手续费上调",
  "scene_040801": "动量因子,长周期>短周期",
  "scene_040802": "动量因子,长周期<短周期",
  "scene_040803": "期限结构因子,长周期>短周期",
  "scene_040804": "期限结构因子,长周期<短周期",
  "scene_040901": "赛道趋同场景",
  "scene_040902": "赛道分歧场景",
  "scene_040903": "因子趋同场景",
  "scene_040904": "因子分歧场景",
  "sector_winrate": "对比赛道胜率",
  "sector_superyield": "对比赛道超额",
  "sector_corryield": "赛道收益相关性",
  "sector_corrdrawback": "赛道回撤相关性",
  "residual_race": "赛道因子回归残差",
  "residual_style": "风格因子回归残差",
  "performance_0101": "年化收益率",
  "performance_0102": "最大回撤",
  "performance_0103": "卡玛比率",
  "performance_0104": "下行标准差",
  "performance_0105": "对比基准胜率",
  "alpha": "风格因子上的超额能力",
  "allocation": "赛道因子上的配置能力",
  "scene_0401": "传统场景适应能力",
  "scene_0403": "特殊场景适应能力",
  "scene_0408": "周期强弱场景",
  "scene_0409": "市场拥挤度场景",
  "sector": "同赛道指标",
  "residual": "残差",
  "performance_overall": "绩效质量",
  "alpha_overall": "Alpha获取能力",
  "allocation_overall": "资产配置能力",
  "scene_overall": "场景应对能力",
  "other_overall": "其他",
  "total": "总分"
}
```
