require 'rubygems'
ActiveRecord::Base.pluralize_table_names=false

# The email queue log file
SALESFORCE_LOGGER = Logger.new("#{RAILS_ROOT}/log/salesforce.log")

class String
  def remove_prefix
    if self.gsub('sf_','') == 'type'
      'class'
    else
      self.gsub('sf_','')
    end
  end
end

class SalesforceSync < ActiveRecord::Schema
                  
  UPDATE_RECORDS_OPTIONS = {
                   Case => {"record_type_id" => "'01230000000001XAAQ'"}
                  }.freeze
                  
  @@logger = SALESFORCE_LOGGER
  
  SYNC_COLUMNS_TO_IGNORE = { Attachment => ['body']}
  
  # Synchrozies SalesForce tables with local tables.
  def self.update_schema
    @@logger.info("(update_schema) :: [#{Time.now}] Updating Schema...")
    
    begin
      AppConstants::CLASS_MAPPINGS.each do |salesforce_class, local_class|
        sync_schema salesforce_class.constantize, local_class.constantize
      end
    rescue
      @@logger.error("(update_schema) :: [#{Time.now}] Failed gracefully !")
    end
    
    @@logger.info("(update_schema) :: [#{Time.now}] Finished Updating Schema.")
  end # self.update_schema
  
  # Updates local tables with the latest data from Salesforce.
  # Accepts an optional array of Salesforce classes to selectively
  # choose which classes to update. If no array is provided, all
  # Salesforce classes are updated. 
  #
  # Examples:
  # #update_records(Account,Case) => Updates Account and Case
  # #update_records => Updates all classes
  def self.update_records(*sf_classes)
    
    if (SfmoltenPost.check_downtime_interval)
        @@logger.info("(update_records) :: [#{Time.now}] MOLTEN downtime scheduled. Exiting ...")
		#        raise "MOLTEN downtime scheduled. Exiting ..."
        return
    end
	
    self.update_schema
    
    mappings = self.build_mapping(sf_classes)
	
    @@logger.info("(update_records) :: [#{Time.now}] Updating Records:")
    mappings.keys.each do |sf_class|
		@@logger.info("#{sf_class}") 
    end
	@@logger.info("*"*80)
    
    begin
      mappings.each do |salesforce_class, local_class|
                  @@logger.info("(update_records) :: salesforce_class=[#{salesforce_class}], local_class=[#{local_class}]")
                  sync_records salesforce_class.constantize, local_class.constantize
      end
    rescue
      @@logger.error("(update_records) :: [#{Time.now}] Failed gracefully !")
    end
    
    @@logger.info("(update_records) :: [#{Time.now}] Finished Updating Records.")
    @@logger.info("*"*80)
    # @@logger.info("[#{Time.now}] Refreshing Cache.")
    # RefreshCache.refresh_all
    # @@logger.info("[#{Time.now}] Finished Refreshing Cache.")
  end
  
  # Builds the mappings that should be used for syncing. 
  def self.build_mapping(sf_classes)
	@@logger.info("(build_mapping) :: (#{sf_classes.any?})")
    if sf_classes.any?
      selected_classes = {}
      sf_classes.each do |sf_class|
        if local_class = AppConstants::CLASS_MAPPINGS[sf_class.to_s]
          selected_classes.merge!({sf_class.to_s => local_class})
        else
          raise "#{sf_class} cannot be synced. It does not exist or has not been added to SYNC_MAPPINGS."
        end
      end # sf_classes.each
      selected_classes
    else
		@@logger.info("(build_mapping) :: Using AppConstants::CLASS_MAPPINGS (this uses all the defined classes rather than a specific class name).")
		AppConstants::CLASS_MAPPINGS
    end # sf_classes.any?
  end
  
  def self.delete_records(salesforce_class,local_class,deleted_ids)
    deleted_ids.each do |id|
      begin
        local_class.destroy(id)
        @@logger.info("(delete_records) :: Deleted #{salesforce_class} with id #{id}")
      rescue Exception => e
		@@logger.error("="*80)
		@@logger.error("Error Occured During delete_records #{e}")       
		@@logger.error("Stack Track of Error----\n #{e.backtrace}")
		@@logger.error("="*80)
		end
    end
  end
  
  def self.do_delete_records(salesforce_class, local_class, updates_from, updates_to)
    # Remove deleted records
	_logger_locale = "(do_delete_records) :: "
	@@logger.info('#{_logger_locale}Retrieving deleted records')
       
    begin
      deleted_ids = salesforce_class.connection.get_deleted(salesforce_class.to_s, updates_from,updates_to)
      @@logger.info("#{_logger_locale}Found [#{deleted_ids.size}] deleted #{salesforce_class} records" )
      delete_records(salesforce_class,local_class,deleted_ids)
    rescue ActiveSalesforce::ASFError
      @@logger.info("#{_logger_locale}Failed to retrieve deleted ids for [#{salesforce_class}]")
      @@logger.info($!.message)
    rescue ActiveRecord::StatementInvalid
      # 2 options:
      # a) no deleted records for this range
      # b) this is a custom object
	  _logger_locale = "(do_delete_records in rescue ActiveRecord::StatementInvalid) :: "
      if $!.message =~ /TypeError: Symbol as array index/ or $!.message =~ /NoMethodError/
        @@logger.info("#{_logger_locale}No #{salesforce_class} records to delete for range #{updates_from} - #{updates_to}") 
      elsif $!.message =~ /not replicable/
        @@logger.info("#{_logger_locale}This class isn't replicable [#{salesforce_class}]")
      else
        @@logger.info("#{_logger_locale}Objects of class [#{salesforce_class}] must be a custom object (this is a normal message and not an error condition because we are recovering from an error).")
        @@logger.info($!.message)
        begin
          @@logger.info("#{_logger_locale}Attempting to find deleted custom objects of class [#{salesforce_class}]")
   
          deleted_ids = salesforce_class.connection.get_deleted((salesforce_class.to_s + '__c'), updates_from, updates_to)
          @@logger.info("#{_logger_locale}Found [#{deleted_ids.size}] deleted #{salesforce_class} records" )
          delete_records(salesforce_class,local_class,deleted_ids)
        rescue ActiveRecord::StatementInvalid
          if $!.message =~ /TypeError: Symbol as array index/
            @@logger.info("#{_logger_locale}No #{salesforce_class} records to delete for range #{updates_from} - #{updates_to}")
          else
            raise
          end
        end # begin
      end # $!.message =~ /TypeError: Symbol as array index/
    end # begin
    
    return deleted_ids
  rescue 
	@@logger.error("="*80)
    @@logger.info("#{_logger_locale}An error occured deleting records")
    @@logger.info($!.message)
    @@logger.info($!.backtrace)
	@@logger.error("="*80)
  end #do_delete_records
  
  def self.sync_records(salesforce_class, local_class)
    @@logger.info("(sync_records) :: Syncing #{salesforce_class.to_s} records with #{local_class.to_s} records")
    
    begin
      sf_cols = salesforce_class.column_names
      local_cols = local_class.column_names

      # find the last locally-updated record
      updates_from, updates_to = self.set_update_range(local_class)
      @@logger.info("(sync_records) :: Update range set to #{updates_from} - #{updates_to}")
      
      # delete records
      deleted_record_ids = do_delete_records(salesforce_class, local_class, updates_from, updates_to)
           
      # grab all records that have been updated on salesforce
      updated_sf_record_ids = if salesforce_class == SelfServiceUser
                                SelfServiceUser.find_by_sql("select Id from SelfServiceUser where LastModifiedDate > #{updates_from}").map { |s| s.id }
                              else                               
                                begin
                                  ids = salesforce_class.connection.get_updated(salesforce_class.to_s, updates_from, updates_to) 
                                  ids || []
                                rescue # could be a custom object
                                  begin
                                    salesforce_class.connection.get_updated("#{salesforce_class.to_s}__c", updates_from, updates_to) 
                                  rescue # might not respond to #get_updated
                                    ids = salesforce_class.find_by_sql("select id from #{salesforce_class.to_s} where LastModifiedDate > #{updates_from}").map { |s| s.id }
                                    @@logger.info("(sync_records) :: Found [#{ids.size}] records of type [#{salesforce_class.to_s}] that need to be updated.")
                                    ids
                                 end
                                end
                              end       
    rescue => e  
		@@logger.error("="*80)
		@@logger.error("Error Occured During sync_records #{e}")       
		@@logger.error("Stack Track of Error----\n #{e.backtrace}")
		@@logger.error("="*80)
      return    
    end 
	begin
		@@logger.info("updated_sf_record_ids=[#{updated_sf_record_ids.to_s}].")
		@@logger.info("Found #{updated_sf_record_ids.size} that need to be updated.")
		@@logger.info("Class: #{updated_sf_record_ids.class}.")
	rescue => e
		@@logger.error("="*80)
		updated_sf_record_ids = []
		@@logger.error("Error Occured During sync_records while reporting results. #{e}")       
		@@logger.error("Stack Track of Error----\n #{e.backtrace}")
		@@logger.error("-"*80)
		@@logger.error("Corrective Action(s):")
		@@logger.error("updated_sf_record_ids = []")
		@@logger.error("-"*80)
		@@logger.error("="*80)
	end
    
    # sync each salesforce record with its associated local record.
    updated_sf_record_ids.each do |updated_id|  
      @@logger.info("updating for id: #{updated_id}")
      # attempt to grab the record...if we find a local record, we do an update. 
      # if we don't find a local record, we do an insert.
      local_record = local_class.find(:first, :conditions => build_conditions_for(salesforce_class,updated_id,'sf_id'))
      sf_record = salesforce_class.find(:first, :conditions => build_conditions_for(salesforce_class,updated_id,'id'))
      if local_record and sf_record
        self.update_record(sf_record,local_record,salesforce_class,local_class)
      elsif sf_record
        self.insert_record(sf_cols,sf_record,salesforce_class,local_class)
      else # sf_record is nil
        @@logger.error("(sync_records) :: Warning - couldn't find the Salesforce Record to meet the conditions:")
        @@logger.error(build_conditions_for(salesforce_class,updated_id,'id'))
      end
      
    end # updated_sf_records
    
  end # self.sync_records
  
  def self.build_conditions_for(salesforce_class, updated_id,id_col)
    conditions = {}
    options = UPDATE_RECORDS_OPTIONS[salesforce_class]
    if options
      conditions.merge!(options)
    end
    id_condition = "#{id_col} = '#{updated_id}' "
    extra_conditions = conditions.to_a.map { |con| con.join('=')  }.join(' AND ')
    [id_condition, extra_conditions.blank? ? nil : extra_conditions].compact.join(' AND ')
  end
  
  def self.insert_record(sf_cols,sf_record,salesforce_class,local_class)
    @@logger.info("(build_conditions_for) :: Inserting new record for #{local_class.to_s} / #{sf_record.id}")
    local_record = local_class.new(self.build_updated_attributes(sf_cols,sf_record,salesforce_class,local_class))
    local_record.sf_id = sf_record.id
    begin
      if local_record.save
        ActiveRecord::Base.connection.execute("update #{local_class.table_name} set sf_id = '#{sf_record.id}' where sf_id='' or sf_id IS NULL")
        # save it again to initialize any associated records
        local_class.find_by_sf_id("#{sf_record.id}").save
        @@logger.info("(build_conditions_for) :: [Successfull Insert] Created #{local_class} / #{local_record.id} / #{local_record.last_modified_date}")
        # deliver the new user email if a contact
        if salesforce_class == Contact
          local_record.send_welcome_email(sf_record.id)
        end
        local_record
      else
        @@logger.info("(build_conditions_for) :: [Failure Insert] #{local_class} / #{sf_record.id}: #{local_record.errors.full_messages.join(',')}")
      end
      return local_class.find_by_sf_id("#{sf_record.id}")
    rescue => e
      local_record.destroy if !local_record.new_record?
      self.report_error(sf_record,'Insert',e)
      local_record
    end
    ActiveRecord::Base.connection.execute("delete from #{local_class.table_name} where sf_id='' or sf_id IS NULL")
    local_record
  end
  
  def self.report_error(sf_record,operation,exception)
	@@logger.error("="*80)
    @@logger.info("[Error #{operation}] #{sf_record.class} / #{sf_record.id}: #{exception}")
    @@logger.info("[Error #{operation}] #{sf_record.class} / #{sf_record.id}: #{exception.backtrace}")
    # Create the error record
    # Error.create!(:error_message => exception,
 #                  :sf_id => sf_record.id,
 #                  :sf_entity => sf_record.class,
 #                  :sql_entity => AppConstants::CLASS_MAPPINGS[sf_record.class.to_s] )
 #    # Send the error email
 #    self.send_error_email(exception)
	@@logger.error("="*80)
  end
  
  def self.send_error_email(exception)
    msg = [ "Subject: MySQL database error\n", "\n", exception ]
    Net::SMTP.start('rye.moltenmagma.com') do |smtp|        
      smtp.sendmail( msg,  'ramya@molten-magma.com', ['ramya@molten-magma.com'] )
    end
  end
  
  def self.update_record(sf_record,local_record,salesforce_class,local_class)
    @@logger.info("(update_record) :: Found a local record...updating #{local_class.to_s} / #{local_record.id}")
    sf_cols = salesforce_class.column_names
    
    # find all of the attributes that have been updated
    updated_attributes = self.build_updated_attributes(sf_cols,sf_record,salesforce_class,local_class,local_record)
    
    # update the local record  
    @@logger.info("(update_record) :: Updating #{local_class} / #{local_record.id}")  
    begin
    if local_record.update_attributes(updated_attributes)
      @@logger.info("(update_record) :: [Successfull Update] Updated #{local_class.to_s} / #{local_record.id} / #{sf_record.system_modstamp}")
    else
      @@logger.info("(update_record) :: [Failure Update] Occurred updating #{local_class.to_s} / #{local_record.id}: #{local_record.errors.full_messages.join(',')}")
    end
    rescue => e
      self.report_error(sf_record,'Update',e)
    end
  end
  
  # Syncronizes the +salesforce_class+ with the +local_class+. 
  def self.sync_schema(salesforce_class,local_class)
    @@logger.info("Syncing #{salesforce_class.to_s} columns with #{local_class.to_s} columns")
    
    sf_cols = salesforce_class.columns
    
    begin
      local_cols = local_class.columns
    rescue
      if $!.message =~ /doesn't exist/
        @@logger.info("(sync_schema) :: Ignoring syncing of schema for #{local_class} as local table doesn't exist.")
        return
      else
        raise
      end
    end
    
    sf_cols.each do |acol|
        colname=acol.name
        colexist="False"
        local_cols.each do |sfacctcol|
          sqlacol=sfacctcol.name
          if(sqlacol.to_s().downcase() == colname.to_s().downcase())
            colexist="True"
          end
        end

        if (colexist.to_s()=="False")
          @@logger.info("(sync_schema) :: Inserting column..... #{colname}")
          add_column local_class.table_name, colname,:string
        end
    end
  end
  
  
  # helper methods for sync_records
  
  def self.set_update_range(local_class)
    order_column = self.set_order_column(local_class)
    last_local_update = local_class.find(:first, :order => "#{order_column} DESC")         
    last_local_update_date = if !last_local_update.nil? and last_local_update.send(order_column) and last_local_update.send(order_column) > 30.days.ago
                              last_local_update.send(order_column)-(15*60) 
                             elsif !last_local_update.nil?
                              # must not be more than 30 days ago per SF
                              28.days.ago-(15*60)  
                             else
                               Time.now.gmtime-(11*60*60*60)
                             end
    [last_local_update_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
     (Time.now.gmtime+(5*30)).strftime("%Y-%m-%dT%H:%M:%SZ")
     ]
  end
  
  # Cases are ordered by created_date. 
  def self.set_order_column(klass)
    # converts a Salesforce class to a local class...
    klass = if klass.ancestors.include? SalesforceRecord
                AppConstants::CLASS_MAPPINGS[klass.to_s].constantize
            else
              klass
            end
    
    if klass == Sfccomment
      "system_modstamp"
    else
      "last_modified_date"
    end
  end
  
  def self.build_updated_attributes(sf_cols,sf_record,salesforce_class,local_class,local_record = nil)
    updated_attributes = {}
    # loop thru each of the salesforce columns and find the updated columns.
    sf_cols.each do |sf_column| 
      next unless sf_value = sf_record.attributes[sf_column]           
      # the id and type columns are mapped to sf_id and sf_type
      local_column = if %w[id type].include? sf_column then "sf_" + sf_column else sf_column end
      updated_attributes.merge!({local_column => sf_value})
      if local_record
        # remove any attributes that weren't changed
        updated_attributes.delete_if do |attribute,value| 
          sf_cols.include?(attribute.remove_prefix) and sf_record.send(attribute.remove_prefix) == local_record.send(attribute) 
        end   
      end
    end # sf_cols
    
     # remove any attributes that should be ignored when syncing
    cols = SYNC_COLUMNS_TO_IGNORE[salesforce_class]
    if cols and cols.any?
      cols.each { |col| updated_attributes.delete(col) }
    end
    
    @@logger.info("(build_updated_attributes) :: [#{salesforce_class.to_s}/#{sf_record.id}] Updated Attributes:")
    updated_attributes.keys.each do |attribute|
      @@logger.info(attribute)
    end
    return updated_attributes
  end
    
end
