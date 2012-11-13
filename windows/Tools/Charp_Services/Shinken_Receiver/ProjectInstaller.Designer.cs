namespace ShinkenReceiverService
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
            this.ReceiverProcessInstaller1 = new System.ServiceProcess.ServiceProcessInstaller();
            this.ReceiverInstaller1 = new System.ServiceProcess.ServiceInstaller();
            // 
            // ReceiverProcessInstaller1
            // 
            this.ReceiverProcessInstaller1.Account = System.ServiceProcess.ServiceAccount.LocalSystem;
            this.ReceiverProcessInstaller1.Installers.AddRange(new System.Configuration.Install.Installer[] {
            this.ReceiverInstaller1});
            this.ReceiverProcessInstaller1.Password = null;
            this.ReceiverProcessInstaller1.Username = null;
            // 
            // ReceiverInstaller1
            // 
            this.ReceiverInstaller1.DisplayName = "Shinken Receiver";
            this.ReceiverInstaller1.ServiceName = "ShinkenReceiver_Service";
            this.ReceiverInstaller1.StartType = System.ServiceProcess.ServiceStartMode.Automatic;
            // 
            // ProjectInstaller
            // 
            this.Installers.AddRange(new System.Configuration.Install.Installer[] {
            this.ReceiverProcessInstaller1});

        }

        #endregion

        private System.ServiceProcess.ServiceProcessInstaller ReceiverProcessInstaller1;
        private System.ServiceProcess.ServiceInstaller ReceiverInstaller1;
    }
}