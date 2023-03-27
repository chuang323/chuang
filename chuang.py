#!groovy
pipeline {
    agent { node { label 'YFV_NODE_22' }}
    parameters {
        
		choice choices: ['YES', 'NO'], description: '''''', name: 'Download'
		choice choices: ['YES', 'NO'], description: '''''', name: 'BUILD_STAGE'
		choice choices: ['true', 'NO'], description: '''''', name: 'DEBUG'

		choice choices: ['YES', 'NO'], description: '''''', name: 'MISRA2012_ANALYSIS'
		choice choices: ['YES', 'NO'], description: '''''', name: 'MISRA2012_COMMIT'
		choice choices: ['YES', 'NO'], description: '''''', name: 'STATIC_ANALYSIS'
		choice choices: ['YES', 'NO'], description: '''''', name: 'STATIC_COMMIT'
		
		choice choices: ['pma_coverity_vip'], description: '''''', name: 'NODE'
		choice choices: ['rebuild','build'], description: '''''', name: 'BUILD_TYPE'
		choice choices: ['DC1E_CN'], description: '''''', name: 'BUILD_VARIANT'
		choice choices: ['dev'], description: '''''', name: 'BRANCH'
    
    }
    environment {
        //General
        JENKINS_EP_NUMBER="26411"     // sample : <MUST> Prebuild / Nightly / Release / Coverity / Unittest /......
        JENKINS_JOB_TYPE='Coverity'
        Gerrit_IP="ssh://172.28.100.196:29418/"
        //REPO
        VIP_VARIANT= "VIP"
        VIP_Repo_URL="""${Gerrit_IP}"""+"26411_PMA/VIP/vip.app"
		// VIP_Common_Repo_URL="""${Gerrit_IP}"""+"30574_BX1E/VIP/vip.app.common"
        VIP_Repo_Branch="dev_A1"
        // VIP_Common_CODE_BRANCH="v1.0-zeekr-BX1E"
        // VIP_Common_DIR="Common"
        // Set cov Stream
        MISRA2012_Stream="GEELY_CDC_BX1E_VIP_MY21_EP26411_MISRAC2012_INT"
        STATIC_Stream="GEELY_CDC_BX1E_VIP_MY21_EP26411_INT"
        // Set time
        def datetime = new java.text.SimpleDateFormat("yyyyMMddHH").format(new Date())
        // Set cov snapshop Name
        MISRA2012_snapshop="${MISRA2012_Stream}_${datetime}"
        STATIC_snapshop="${STATIC_Stream}_${datetime}"

        // Set cov Env
        user="admin"
        password="coverity"
        cov_root="C:\\coverity\\cov-analysis-win64-2020.03\\"
        MISRA2012_config="${cov_root}config\\coding-standards\\misrac2012\\misrac2012-mandatory-required.config"
        STATIC_config="${cov_root}config\\coding-standards\\cert-c\\cert-c-all.config"

        // Set Path Env
        cov_temp="D:\\Coverity_temp\\${JENKINS_EP_NUMBER}\\${BUILD_VARIANT}"
        build_script="${VIP_WORKSPACE}\\Build\\make\\integration.bat"
        //Workspace
        LINUX_WORKSPACE = "/home/admins/Jenkins"
        WINDOWS_WORKSPACE = "D:\\Jenkins"
		VIP_WORKSPACE="""${WINDOWS_WORKSPACE}"""+"\\"+"""${JENKINS_EP_NUMBER}"""+"\\"+"""${JENKINS_JOB_TYPE}"""+"\\"+"""${VIP_VARIANT}"""+"_"+"""${BUILD_VARIANT}"""+"_"+"""${BRANCH}"""
		

       
    }
    options {
        buildDiscarder logRotator(artifactDaysToKeepStr: '', artifactNumToKeepStr: '', daysToKeepStr: '300', numToKeepStr: '60')
        timestamps()
        disableConcurrentBuilds()
    }    
    stages {
       stage('env'){
            agent { node { label """${NODE}""" ; customWorkspace """${VIP_WORKSPACE}""" }}
            steps{
               script {
                    echo "work_dir: ${VIP_WORKSPACE}"
                    echo "cov_temp: ${cov_temp}"
                    echo "MISRA2012_snapshop: ${MISRA2012_snapshop}"
                    echo "STATIC_snapshop: ${STATIC_snapshop}"
                }
               
             
            }
        }
        stage('Download'){
            when { expression { 'YES' in Download }}
            agent { node { label """${NODE}""" ; customWorkspace """${VIP_WORKSPACE}""" }}
            steps{
               script {
                    checkout([$class: 'GitSCM', branches: [[name: """${VIP_Repo_Branch}"""]], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'CloneOption', depth: 0, noTags: false, reference: '', shallow: false]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'HSHU2018', url: """${env.VIP_Repo_URL}"""]]])
                    // checkout([$class: 'GitSCM', branches: [[name: """${VIP_Common_CODE_BRANCH}"""]], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: "${VIP_Common_DIR}"], [$class: 'CloneOption', depth: 0, noTags: false, reference: '', shallow: false]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'HSHU2018', url: """${env.VIP_Common_Repo_URL}"""]]])				
                    echo "================================"
                    echo """${BUILD_STAGE}"""
                }
               
             
            }
        }
        stage('Build'){
            when { expression { 'YES' in """${BUILD_STAGE}""" }}
            agent { node { label """${NODE}""" ; customWorkspace """${VIP_WORKSPACE}""" }}
            steps{
                wrap([$class: 'BuildUser'])
                {
                    bat label: '', script: '''
                        %cov_root%bin\\cov-build.exe --dir %cov_temp%\\origin --emit-complementary-info %build_script%
                        '''
                }
               
            }
        }
        stage('Analysis') {
            parallel {
                stage('MISRA2012') {
                    agent { node { label """${NODE}""" ; customWorkspace """${VIP_WORKSPACE}""" }}
                    environment {
                        temp_dir="${cov_temp}\\MISRA2012"
                    }
                    stages {
                        stage('MISRA2012_ANALYSIS') {
                            when { expression { 'YES' in MISRA2012_ANALYSIS }}
                            steps {
                                wrap([$class: 'BuildUser'])
                                {
                                    bat label: '', script: '''
                                        del /q /f %temp_dir%
                                        mkdir %temp_dir%
                                        xcopy /s /y %cov_temp%\\origin\\*.* %temp_dir% 
                                        %cov_root%bin\\cov-analyze.exe --dir  %temp_dir%  --strip-path=%VIP_WORKSPACE% --coding-standard-config %MISRA2012_config%
                                        '''
                                }
                            }
                        }
                        stage('MISRA2012_COMMIT') {
                            when { expression { 'YES' in MISRA2012_COMMIT }}
                            steps {
                                wrap([$class: 'BuildUser'])
                                {
                                    bat label: '', script: '''
                                        %cov_root%bin\\cov-commit-defects.exe --dir  %temp_dir%  --user %user% --password %password% -host 172.30.181.115 --stream %MISRA2012_Stream% --description %MISRA2012_snapshop% --snapshot-id-file %cov_temp%\\snapshot-id.txt
                                        '''
                                }
                            }
                        }
                    }
                }                    
                stage('STATIC') {      
                    agent { node { label """${NODE}""" ; customWorkspace """${VIP_WORKSPACE}""" }}  
                    environment {
                        temp_dir="${cov_temp}\\STATIC"
                    }
                    stages { 
                        stage('STATIC_ANALYSIS')  {
                            when { expression { 'YES' in STATIC_ANALYSIS }}
                            steps {
                                wrap([$class: 'BuildUser'])
                                {
                                    bat label: '', script: '''
                                        del /q /f %temp_dir%\\*.*
                                        mkdir %temp_dir%
                                        xcopy /s /y %cov_temp%\\origin\\*.* %temp_dir% 
                                        %cov_root%bin\\cov-analyze.exe --dir  %temp_dir%  --strip-path=%VIP_WORKSPACE% --coding-standard-config %STATIC_config% 
                                    '''
                                }
                            }
                        }
                        stage('STATIC_COMMIT') {
                            when { expression { 'YES' in STATIC_COMMIT }}    
                            steps {
                                wrap([$class: 'BuildUser'])
                                {
                                    bat label: '', script: '''
                                        %cov_root%bin\\cov-commit-defects.exe --dir  %temp_dir%  --user %user%  --password %password% -host 172.30.181.115 --stream %STATIC_Stream% --description %STATIC_snapshop% --snapshot-id-file %cov_temp%\\snapshot-id.txt
                                    '''
                                }
                            }
                        }
                    }
                }
            }
        }
        
    }
}
   



