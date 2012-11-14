namespace ShinkenBrokerService
{
    partial class ProjectInstaller
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary> 
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Component Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            this.BrokerProcessInstaller1 = new System.ServiceProcess.ServiceProcessInstaller();
            this.BrokerInstaller1 = new System.ServiceProcess.ServiceInstaller();
            // 
            // BrokerProcessInstaller1
            // 
            this.BrokerProcessInstaller1.Account = System.ServiceProcess.ServiceAccount.LocalSystem;
            this.BrokerProcessInstaller1.Installers.AddRange(new System.Configuration.Install.Installer[] {
            this.BrokerInstaller1});
            this.BrokerProcessInstaller1.Password = null;
            this.BrokerProcessInstaller1.Username = null;
            // 
            // BrokerInstaller1
            // 
            this.BrokerInstaller1.DisplayName = "Shinken Broker";
            this.BrokerInstaller1.ServiceName = "ShinkenBroker_Service";
            this.BrokerInstaller1.StartType = System.ServiceProcess.ServiceStartMode.Automatic;
            // 
            // ProjectInstaller
            // 
            this.Installers.AddRange(new System.Configuration.Install.Installer[] {
            this.BrokerProcessInstaller1});

        }

        #endregion

        private System.ServiceProcess.ServiceProcessInstaller BrokerProcessInstaller1;
        private System.ServiceProcess.ServiceInstaller BrokerInstaller1;
    }
}