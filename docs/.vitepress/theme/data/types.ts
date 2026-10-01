export type Level = 'easy' | 'mid' | 'hard'

export interface Article {
  /** 折叠分组名，如 'Linux'、'入门与基础' */
  group: string
  /** 行标题 */
  title: string
  /** 站内绝对路径，如 '/guide/linux-install'，不带 .html */
  link: string
  /** 副标题 / 一句话描述 */
  sub?: string
  /** 标签数组 */
  tags?: string[]
  /** 难度；缺省不显示难度色标 */
  lvl?: Level
  /** YYYY-MM-DD；缺省不显示日期 */
  date?: string
}
