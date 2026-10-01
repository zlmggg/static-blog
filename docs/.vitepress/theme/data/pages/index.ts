import type { Article } from '../types'
import casesIndex from './cases-index'
import casesTroubleshooting from './cases-troubleshooting'
import guideLinux from './guide-linux'
import guideServices from './guide-services'
import guideData from './guide-data'
import guideMonitor from './guide-monitor'
import guideContainer from './guide-container'
import guideAutomation from './guide-automation'
import guideDevops from './guide-devops'
import guideAiops from './guide-aiops'
import guideArchitecture from './guide-architecture'
import guideBlog from './guide-blog'
import guideCareer from './guide-career'
import guideDevopsDev from './guide-devops-dev'
import interviewIndex from './interview-index'
import advanced from './advanced'

export const pages: Record<string, Article[]> = {
  '/cases/': casesIndex,
  '/cases/troubleshooting': casesTroubleshooting,
  '/guide/linux': guideLinux,
  '/guide/services': guideServices,
  '/guide/data': guideData,
  '/guide/monitor': guideMonitor,
  '/guide/container': guideContainer,
  '/guide/automation': guideAutomation,
  '/guide/devops': guideDevops,
  '/guide/aiops': guideAiops,
  '/guide/architecture': guideArchitecture,
  '/guide/blog': guideBlog,
  '/guide/career': guideCareer,
  '/guide/devops-dev': guideDevopsDev,
  '/interview/': interviewIndex,
  '/roadmap': advanced
}
