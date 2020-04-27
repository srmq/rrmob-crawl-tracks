def yesterdayStr = ''

pipeline {
   agent { label 'mesos' }

   stages {
      stage('Checkout') {
         steps {
            // Get some code from a GitHub repository
            git 'https://github.com/srmq/rrmob-crawl-tracks.git'

            // Create python3 venv.
            sh "python3 -m venv ./venv"
            
            //download python dependencies to venv
            sh """
            . ./venv/bin/activate
            pip3 install -r ./requirements.txt
            """
         }
      }
      stage('Run') {
         steps {
            script {
               def yesterday = (new Date()).minus(1)
               yesterdayStr = yesterday.format('yyyy-MM-dd')
            }
            withCredentials(bindings: [usernamePassword(credentialsId: 'rrmob-spotify-crawler-db-user', \
                                                        usernameVariable: 'DBUSER', \
                                                        passwordVariable: 'DBPASS'), \
                                       string(credentialsId: 'rrmob-ms-server-root-pass', \
                                              variable: 'ROOTPASS')]) {
               sh """
               . ./venv/bin/activate
               python3 ./startup.py crawl -c ${ROOTPASS} ${yesterdayStr} -d postgres://${DBUSER}:${DBPASS}@tamandare.cin.ufpe.br:5432/spotcrawler
               """
            }
         }
      }
   }
}
