require 'digest/md5'
module  AuthenticationSystem
  module  ContactMethods
      def self.included(base)
      base.class_eval do 
        #------------------
        # VALIDATIONS
        #------------------
        validates_presence_of :portal_password__c, :if => :validate_password?, :on => :update
        validates_confirmation_of :portal_password__c, :if => :validate_password?, :on => :update
        validates_length_of :portal_password__c, { :within => 5..40, :if => :validate_password?, :on => :update }
        
      end
      base.extend(ClassMethods)    
    end    

    module ClassMethods
      def authenticate(email,password, request = nil)
        contact = Sfcontact.find(:first, :include => [:sfssl],
                                    :conditions => ["sfssl.username = ? AND sfcontact.portal_password__c = ? AND sfcontact.contact_status__c = ? AND sfcontact.portal_privilege__c IN (?)",
                                                    email,password,"Active",AppConstants::PRIVILEGES_WITH_ACCESS])
        if contact
          begin
            contact.update_login_success!(request)
          rescue  SocketError
            flash[:notice] = "Unable to connect to Salesforce"
            logger.info("Unable to connect to Salesforce")
          end
          return contact
        else
          contact = Sfcontact.find(:first, 
                                      :conditions => ["sfcontact.portal_username__c = ? AND sfcontact.portal_password__c = ? AND sfcontact.contact_status__c = ? AND sfcontact.portal_privilege__c IN (?)",
                                                      email,password,"Active",AppConstants::PRIVILEGES_WITH_ACCESS])
          if contact
            begin
              contact.update_login_success!(request)
            rescue  SocketError
              flash[:notice] = "Unable to connect to Salesforce"
              logger.info("Unable to connect to Salesforce")
            end
            return contact
          else
            logger.info("Failed to login contact with email [#{email}] and pw [#{password}]")
            contacts = Sfcontact.find_all_by_email(email)
            if contacts.size == 1
              contact = contacts.first
              contact.update_login_failure!
            else
              # don't know which contact failed to login.
            end
            return nil
          end
        end
      end
      
      def authenticate_by_id(id)
        if contact = Sfcontact.find(:first, :include => [:settings], 
                         :conditions => ["sf_id COLLATE latin1_bin LIKE ? and contact_status__c = ?", id+'%',"Active"])
          contact.update_login_success!
          return contact
        else
          logger.info("Failed to login contact via id [#{id}]")
          if contact = Sfcontact.find_by_sf_id(id)
            contact.update_login_failure!
          end
          return nil
        end
      end

      # used to login via cookie
      def authenticate_by_token(id, token)
        if contact = Sfcontact.find(:first, :include => [:settings], 
                         :conditions => ["sf_id = ? AND sfcontact_setting.token = ? and contact_status__c = ?", id,token,"Active"])
          contact.update_login_success!
          return contact
        else
          logger.info("Failed to login contact via token with id [#{id}] and token [#{token}]")
          if contact = Sfcontact.find_by_sf_id(id)
            contact.update_login_failure!
          end
          return nil
        end
      end
      
      def find_by_id_and_token(id,token)
        find(:first, :include => [:settings], 
                     :conditions => ["sfcontact.sf_id = ? AND sfcontact_setting.token = ?", id, token])
      end

      # Emails instructions on retrieving the password to the Sfcontact with the +email+ address. 
      # The Sfcontact with the +email+ is returned if a Sfcontact is found. Otherwise nil is returned.
      # port - the port of the request...should be provided in the controller as "request.port_string"
      # host - Can also provide a host...default to the local host.
      def forgot_password(email, port, host = 'localhost')      
        begin
          if contact = Sfssl.find_by_username(email).sfcontact
            SfcontactMailer.deliver_forgot_password(contact,port,host)
            return contact
          end
        rescue NoMethodError
          # no user found
        end
      end
    end # ClassMethods
    
    # Some integers are stored as strings. This increments these. 
    def increment_string!(attribute)
      return if RAILS_ENV == 'test'
      synced_record.update_attribute(attribute,synced_record.send(attribute).to_f + 1)
    end

    # Changes the contact's password, saves the record, and updates the associated SF record.
    # Self is returned.
    # DEREK - DIDN'T WANT TO HANDLE THIS WAY, BUT CALLBACKS AREN'T UPDATING SF RECORDS.
    def change_password!(new_pass, new_pass_confirmation)   
      @change_password = true   
      self.portal_password__c = new_pass
      self.portal_password__c_confirmation = new_pass_confirmation
      if save
        update_salesforce_attribute('portal_password__c')
      end
      return self
    end
    
    # Verifies and saves the account. 
    def verified!
      update_attribute('verified',1)
    end

    # Updates the user's +last_logged_in_at+ time and returns self.
    def after_log_in!
      update_attribute('logged_in_at',Time.now)
      return self
    end
    
    # SF IS THROWING ERRORS WHEN TRYING TO UPDATE DATES
    # Updates the login time and the successful login count when a user successfully authenticates.
    def update_login_success!(request = nil)
      # update sf with gmtime
      update_attribute_and_sync('portal_last_login_date__c',Time.now.gmtime)
      ### ALSO WANT IP OF THE SERVER...BUT NOT SURE HOW TO GRAB IT
      update_attribute_and_sync('portal_last_version__c',"#{request.host} #{AppConstants::MOLTEN_VERSION}") if request
      increment_string!('portal_login_count__c')
    end
    
    # Updates the last login failure date and and the failed login count when a user fails to authenticate
    def update_login_failure!
      # update sf with gmtime
      update_attribute_and_sync('portal_last_login_fail_date__c',Time.now.gmtime)
      increment_string!('portal_login_fail_count__c')
    end
    
    # Returns the value of +#settings.token+ if it is not nil. Otherwise,
    # we generate a new token, save it, and return it.
    def token
      return unless settings
      if settings.token.nil?
        settings.update_attribute('token',generate_token)
        return settings.token
      else
        return settings.token
      end
    end
    
    private
    
    # Generates a new token but does not save it to the +token+ attribute.
    def generate_token
      logger.info("generating token for #{id} email: #{email} name: #{name}")
      token_before = "#{Time.now.to_i}" + email
      # MD5.md5(token_before).hexdigest
      OpenSSL::HMAC.hexdigest(OpenSSL::Digest::Digest.new(AppConstants::FILE_DOWNLOAD_DIGEST), 
                                                                AppConstants::FILE_DOWNLOAD_KEY, token_before)
    end

    def validate_password?
      @change_password
      # portal_password__c or new_record?
    end

    # Sends a welcome message to the user
    def deliver_welcome
      UserMailer.deliver_welcome(self)
    end
  end # ContactMethods
end # AuthenticationSystem