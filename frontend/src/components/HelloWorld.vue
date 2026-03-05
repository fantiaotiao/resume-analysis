<template>
  <div class="resume-analysis">
    <h1 class="title">—— AI赋能简历分析，精准匹配每一份可能 ——</h1>

    <!-- 核心交互区：上传 + 岗位需求 + 提交 -->
    <div class="interactive-area">
      <!-- 1. PDF简历上传（单文件、格式/大小校验） -->
      <div class="file-upload">
        <el-upload
          class="upload-demo"
          drag
          :auto-upload="false"  
          :on-change="handleFileChange" 
          :before-upload="beforeUpload"  
          accept=".pdf"  
          :limit="1" 
          :on-exceed="handleExceed"  
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将PDF简历拖到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              只能上传单个PDF文件，且不超过500kb
            </div>
          </template>
        </el-upload>
      </div>
      <div class="title1">—— 岗位需求 ——</div>
      <!-- 2. 岗位需求 -->
      <div class="job-demand">
        <el-form label-width="120px" :model="jobDemandForm" class="job-demand-form">
          <!-- 2.1 技能要求：输入框（支持多个技能，逗号分隔） -->
          <el-form-item label="技能要求" prop="skills">
            <el-input
              v-model="jobDemandForm.skills"
              placeholder="请输入所需技能，多个技能用逗号分隔（如：Java,SpringBoot,MySQL）"
              style="width: 800px;"
            ></el-input>
          </el-form-item>

          <!-- 2.2 工作经验：下拉选择 + 补充说明 -->
          <el-form-item label="工作经验" prop="workExperience">
            <el-select
              v-model="jobDemandForm.workExperience"
              placeholder="请选择所需工作经验"
              style="width: 300px; margin-right: 20px;"
            >
              <el-option label="不限" value="不限"></el-option>
              <el-option label="应届生" value="应届生"></el-option>
              <el-option label="1年以下" value="1年以下"></el-option>
              <el-option label="1-3年" value="1-3年"></el-option>
              <el-option label="3-5年" value="3-5年"></el-option>
              <el-option label="5-10年" value="5-10年"></el-option>
              <el-option label="10年以上" value="10年以上"></el-option>
            </el-select>
            <el-input
              v-model="jobDemandForm.workExperienceDesc"
              placeholder="补充说明（如：需有大型项目经验）"
              style="width: 480px;"
            ></el-input>
          </el-form-item>

          <!-- 2.3 学历要求-->
          <el-form-item label="学历要求" prop="education">
            <el-select
              v-model="jobDemandForm.education"
              placeholder="请选择所需学历"
              style="width: 800px;"
            >
              <el-option label="不限" value="不限"></el-option>
              <el-option label="高中/中专" value="高中/中专"></el-option>
              <el-option label="大专" value="大专"></el-option>
              <el-option label="本科" value="本科"></el-option>
              <el-option label="硕士" value="硕士"></el-option>
              <el-option label="博士" value="博士"></el-option>
            </el-select>
          </el-form-item>

          <!-- 2.4 其他要求 -->
          <el-form-item label="其他要求" prop="otherRequirements">
            <el-input
              type="textarea"
              v-model="jobDemandForm.otherRequirements"
              placeholder="请输入其他岗位需求（如：沟通能力、证书要求、出差要求等）"
              rows="3"
              style="width: 800px;"
            ></el-input>
          </el-form-item>
        </el-form>
      </div>

      <!-- 3. 提交按钮 -->
      <div class="submit-btn">
        <el-button 
          type="primary" 
          size="large" 
          @click="handleSubmit"
          :disabled="!selectedFile || !checkJobDemandComplete()" 
        >
          解析简历并匹配岗位
        </el-button>
      </div>
    </div>

    <!-- 结果展示模块：分类展示 -->
    <div class="result-area" v-if="showResult">
      <h2 class="result-title">简历分析结果</h2>

      <!-- 3.1 基本信息 -->
      <div class="result-card">
        <el-card header="基本信息" shadow="hover" style="width: 800px; margin-bottom: 20px;">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="姓名">{{ resumeData.basicInfo.name || '待解析' }}</el-descriptions-item>
            <el-descriptions-item label="电话">{{ resumeData.basicInfo.phone || '待解析' }}</el-descriptions-item>
            <el-descriptions-item label="邮箱">{{ resumeData.basicInfo.email || '待解析' }}</el-descriptions-item>
            <el-descriptions-item label="地址">{{ resumeData.basicInfo.address || '待解析' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </div>

      <!-- 3.2 求职信息 -->
      <div class="result-card">
        <el-card header="求职信息" shadow="hover" style="width: 800px; margin-bottom: 20px;">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="求职意向">{{ resumeData.jobInfo.intention || '待解析' }}</el-descriptions-item>
            <el-descriptions-item label="期望薪资">{{ resumeData.jobInfo.salary || '待解析' }}</el-descriptions-item>
            <el-descriptions-item label="工作年限">{{ resumeData.jobInfo.workYears || '待解析' }}</el-descriptions-item>
            <el-descriptions-item label="学历背景">{{ resumeData.jobInfo.education || '待解析' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </div>

      <!-- 3.3 匹配评分 -->
      <div class="result-card">
        <el-card header="岗位匹配评分" shadow="hover" style="width: 800px;">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="技能匹配率">
              <el-progress :percentage="resumeData.matchScore.skillMatchRate" status="success"></el-progress>
              <span class="score-text">{{ resumeData.matchScore.skillMatchRate }}%</span>
            </el-descriptions-item>
            <el-descriptions-item label="经验相关性">
              <el-progress :percentage="resumeData.matchScore.experienceRelevance" status="success"></el-progress>
              <span class="score-text">{{ resumeData.matchScore.experienceRelevance }}%</span>
            </el-descriptions-item>
            <el-descriptions-item label="综合匹配度" span="2">
              <el-progress :percentage="resumeData.matchScore.overallMatch" status="success" style="width: 100%;"></el-progress>
              <span class="score-text">{{ resumeData.matchScore.overallMatch }}%</span>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script>
// 1. 引入axios
import axios from 'axios';
import { UploadFilled } from '@element-plus/icons-vue'

export default {
  name: 'ResumeAnalysis',
  components: {
    UploadFilled
  },
  data() {
    return {
      selectedFile: null,  
      showResult: false,   
      jobDemandForm: {
        skills: '',               
        workExperience: '',       
        workExperienceDesc: '',   
        education: '',            
        otherRequirements: ''     
      },
      // 简历数据（和后端返回的JSON结构完全对应）
      resumeData: {
        basicInfo: {
          name: '',
          phone: '',
          email: '',
          address: ''
        },
        jobInfo: {
          intention: '',
          salary: '',
          workYears: '',
          education: ''
        },
        matchScore: {
          skillMatchRate: 0,
          experienceRelevance: 0,
          overallMatchScore: 0
        }
      }
    }
  },
  methods: {
    handleFileChange(file) {
      this.selectedFile = file.raw;
    },
    handleExceed() {
      this.$message.warning('只能上传一个PDF简历文件！');
    },
    beforeUpload(file) {
      const isPDF = file.type === 'application/pdf';
      if (!isPDF) {
        this.$message.error('只能上传PDF格式的文件！');
        return false;
      }
      const isLt500K = file.size / 1024 < 500;
      if (!isLt500K) {
        this.$message.error('文件大小不能超过500kb！');
        return false;
      }
      return true;
    },
    checkJobDemandComplete() {
      return !!this.jobDemandForm.skills || !!this.jobDemandForm.workExperience || !!this.jobDemandForm.education;
    },

    // 2. 后端接口
    handleSubmit() {
      // 加载提示
      this.$message.info('正在解析简历并匹配岗位，请稍候...');
      
      // 校验：选中了PDF文件
      if (!this.selectedFile) {
        this.$message.error('请先上传PDF简历文件！');
        return;
      }

      // 构建FormData（后端要求的参数格式：文件+表单字段）
      const formData = new FormData();
      // 1. 添加上传的PDF文件
      formData.append('file', this.selectedFile);
      // 2. 添加岗位需求字段（和后端接口参数一一对应）
      formData.append('skills', this.jobDemandForm.skills);
      formData.append('workExperience', this.jobDemandForm.workExperience);
      formData.append('workExperienceDesc', this.jobDemandForm.workExperienceDesc);
      formData.append('education', this.jobDemandForm.education);
      formData.append('otherRequirements', this.jobDemandForm.otherRequirements);

      // 调用后端接口
      axios.post('http://localhost:8888/analyze_resume', formData, {
        // 必须设置Content-Type为multipart/form-data（文件上传专用）
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        // 超时时间：10秒（避免AI处理慢导致超时）
        timeout: 10000
      }).then(res => {
        // 接口调用成功：把后端返回的JSON赋值给resumeData
        this.resumeData = res.data;
        // 显示结果区域
        this.showResult = true;
        // 成功提示
        this.$message.success('简历解析和匹配完成！');
      }).catch(err => {
        // 错误处理：显示具体的错误信息
        const errorMsg = err.response?.data?.detail || err.message || '接口调用失败';
        this.$message.error(`解析失败：${errorMsg}`);
        // 隐藏结果区域
        this.showResult = false;
      });
    }
  }
}
</script>

<style scoped>
/* 整体样式 */
.resume-analysis {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: "Microsoft YaHei", sans-serif;
}

/* 标题样式 */
.title {
  text-align: center;
  color: #1989fa;
  margin-bottom: 40px;
}

.title1 {
  text-align: center;
  color: #000000;
  margin-bottom: 16px;
}

/* 交互区域样式 */
.interactive-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 30px;
  margin-bottom: 50px;
}

/* 上传区域样式 */
.file-upload {
  width: 800px;
}

/* 岗位需求表单样式 */
.job-demand {
  width: 800px;
}
.job-demand-form {
  display: flex;
  flex-direction: column;
  gap: 20px;  /* 增加表单项间距，提升美观度 */
}

/* 提交按钮样式 */
.submit-btn {
  margin-top: 10px;
}

/* 结果展示区域样式 */
.result-area {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.result-title {
  color: #409eff;
  margin-bottom: 20px;
}

/* 结果卡片样式 */
.result-card {
  width: 800px;
  margin-bottom: 20px;
}

/* 评分文本样式 */
.score-text {
  margin-left: 10px;
  font-weight: bold;
  color: #67c23a;
}
</style>