# Filters added to this controller will be run for all controllers in the application.
# Likewise, all the methods added will be available for all controllers.
class ApplicationController < ActionController::Base
  @BATCH_SIZE=50

  def updateAccount()
      puts "Updating Account Object .........."
      begin 
        @sfcol=Account.columns
        @sqlcol=Sfaccount.columns
        @sfaccts=Account.find(:all, :limit => 3000) 
      rescue => e  
        logger.error(e)        
        puts "Error in Querying Account data: ", $!, "\n"
        print "ERROR IN Querying Account data:"+e                       
        #sendEmail(e) 
      end
                      
      @sfaccts.each do |sfa|                       
        tempHash = Hash.new()
        @id=nil
          @sfcol.each do |acol|            
            @sf_id=sfa.id
            @ifUpdate=Sfaccount.find(:first, :conditions => "sf_id = '#{@sf_id}'")
            if (@ifUpdate)
              @id=@ifUpdate.id
            end
            @field=acol.name 
            #puts " Field............... #{@field}"      
            @value=sfa.send("#{@field}")      
            #puts " Value............... #{@value}"
            
            if(@value!=nil)
              if(@field.to_s().downcase()=="id")
                @field="sf_id"              
              
              end
              tempHash["#{@field}"]=@value          
            end         
          end                                 
        
          begin   
            if(@id !=nil)   
              sqlUpdate=Sfaccount.find(@id)
              sqlUpdate.update_attributes(tempHash)
              sqlUpdate.save
            else      
              sacct=Sfaccount.new(tempHash)
              sacct.save
              @msg="Succesfully Inserted the records....."
            end
          rescue => e
            logger.error(e)
            id=tempHash["sf_id"]
            puts "Error in inserting data: ", $!, "\n"
            print "ERROR IN INSERTING DATA:"+e              
            updateErrorTable(e,"Account","Sfaccount",id) 
            sendEmail(e)                     
         end  
      end            
      return @msg
    end 
  
    def updateCase()
        puts "Updating Case Object .........."
        begin        
          @sfcol=Case.columns
          @sqlcol=Sfcase.columns
          @sfaccts=Case.find(:all, :limit => 100) 
          
          
          #@sfaccts=Case.find_by_sql("select * from Case where createdDate < 2004-01-01T00:00:00Z limit 5000")
          @queryLen=(@sfaccts.length).to_i
          #puts "Number of Cases records that need to be inserted are #{@queryLen}"
          
          
        rescue => e  
          logger.error(e)        
          puts "Error in Querying Case data: ", $!, "\n"
          print "ERROR IN Querying Case data:"+e                       
          #sendEmail(e) 
        end    
        @sfaccts.each do |sfa|                           
          tempHash = Hash.new()
          @id=nil
          @sfcol.each do |acol|            
            @sf_id=sfa.id
            @ifUpdate=Sfcase.find(:first, :conditions => "sf_id = '#{@sf_id}'")
            if (@ifUpdate)
              @id=@ifUpdate.id
            end
            @field=acol.name 
            #puts " Field............... #{@field}"      
            @value=sfa.send("#{@field}")      
            #puts " Value............... #{@value}"
            
            if(@value!=nil)
              if(@field.to_s().downcase()=="id")
                @field="sf_id"
              end
              #if(@field.to_s().downcase()=="type")
                #puts "Field name is Type and value is .....#{@value}"
                #@field="sf_type"
              #end
              
              tempHash["#{@field}"]=@value          
            end         
          end                                   
            
          begin  
              if(@id !=nil)   
                sqlUpdate=Sfcase.find(@id)
                sqlUpdate.update_attributes(tempHash)
                sqlUpdate.save
              else         
                sacct=Sfcase.new(tempHash)
                sacct.save
                @msg="Succesfully Inserted the records....."
              end
          rescue => e
              logger.error(e)
              id=tempHash["sf_id"]
              puts "Error in inserting data: ", $!, "\n"
              print "ERROR IN INSERTING CASE RECORD:"+e              
              updateErrorTable(e,"Case","Sfcase",id) 
              sendEmail(e)                     
          end  
        end            
        return @msg
      end 
      
      def updateUser()
        puts "Updating User Object .........."
        begin
          @sfcol=User.columns
          @sqlcol=Sfuser.columns
          @sfusers=User.find(:all, :limit => 1000)  
        rescue => e  
          logger.error(e)        
          puts "Error in Querying User data: ", $!, "\n"
          print "ERROR IN Querying User data:"+e                       
          #sendEmail(e) 
        end   
          
        @sfusers.each do |sfa|           
          tempHash = Hash.new()
          @id=nil
          @sfcol.each do |acol|            
            @sf_id=sfa.id
            @ifUpdate=Sfuser.find(:first, :conditions => "sf_id = '#{@sf_id}'")
            if (@ifUpdate)
              @id=@ifUpdate.id
            end
            @field=acol.name 
            #puts " Field............... #{@field}"      
            @value=sfa.send("#{@field}")      
            #puts " Value............... #{@value}"
            
            if(@value!=nil)
              if(@field.to_s().downcase()=="id")
                @field="sf_id"
              end
              tempHash["#{@field}"]=@value          
            end         
          end   
          begin  
              if(@id !=nil)   
                sqlUpdate=Sfuser.find(@id)
                sqlUpdate.update_attributes(tempHash)
                sqlUpdate.save
              else    
                sacct=Sfuser.new(tempHash)              
                sacct.save
              end
              
              @msg="Succesfully Inserted the records....."
          rescue => e
              logger.error(e)
              id=tempHash["sf_id"]
              puts "Error in inserting data: ", $!, "\n"
              print "ERROR IN INSERTING DATA:"+e              
              updateErrorTable(e,"User","Sfuser",id) 
              sendEmail(e)                     
          end                
            
        end            
        return @msg
      end 
      
      
      def updateSSL()
        puts "Updating Self Service User Object .........."
        begin
          @sfcol=SelfServiceUser.columns
          @sqlcol=Sfssl.columns
          @sfssl=SelfServiceUser.find(:all, :limit => 3000)
        rescue => e  
          logger.error(e)        
          puts "Error in Querying SSL data: ", $!, "\n"
          print "ERROR IN Querying SSL data:"+e                       
          #sendEmail(e) 
        end     
        
        @sfssl.each do |sfa|               
          tempHash = Hash.new()
          @id=nil
          @sfcol.each do |acol|            
            @sf_id=sfa.id
            @ifUpdate=Sfssl.find(:first, :conditions => "sf_id = '#{@sf_id}'")
            if (@ifUpdate)
              @id=@ifUpdate.id
            end
            @field=acol.name 
            #puts " Field............... #{@field}"      
            @value=sfa.send("#{@field}")      
            #puts " Value............... #{@value}"
            
            if(@value!=nil)
              if(@field.to_s().downcase()=="id")
                @field="sf_id"
              end
              tempHash["#{@field}"]=@value          
            end         
          end                                   
            
          begin  
              if(@id !=nil)   
                sqlUpdate=Sfssl.find(@id)
                sqlUpdate.update_attributes(tempHash)
                sqlUpdate.save
              else                  
                sacct=Sfssl.new(tempHash)
                sacct.save
                @msg="Succesfully Inserted the records....."
              end
          rescue => e
              logger.error(e)
              id=tempHash["sf_id"]
              puts "Error in inserting data: ", $!, "\n"
              print "ERROR IN INSERTING CASE RECORD:"+e              
              updateErrorTable(e,"SelfServiceUser","Sfssl",id) 
              sendEmail(e)                  
          end               
            
        end            
        return @msg
      end 
      
      def updateContact()
        puts "Updating Contact Object .........."
        begin
          @sfcol=Contact.columns
          @sqlcol=Sfcontact.columns
          #@sfcont=Contact.find(:all, :limit => 17000)    
          @sfcont=Contact.find(:all, :conditions => "account_id = '00130000000ODT9AAO' or account_id = '00130000000M4oKAAS' or account_id = '00130000004hcgiAAA' or account_id = '001300000019kKMAAY'" ,:limit => 2000)
        rescue => e  
          logger.error(e)        
          puts "Error in Querying Contact data: ", $!, "\n"
          print "ERROR IN Querying Contact data:"+e                       
          #sendEmail(e) 
        end   
        
        @sfcont.each do |sfa|                                  
          tempHash = Hash.new()
          @id=nil
          @sfcol.each do |acol|            
            @sf_id=sfa.id
            @ifUpdate=Sfcontact.find(:first, :conditions => "sf_id = '#{@sf_id}'")
            if (@ifUpdate)
              @id=@ifUpdate.id
            end
            @field=acol.name 
            #puts " Field............... #{@field}"      
            @value=sfa.send("#{@field}")      
            #puts " Value............... #{@value}"
            
            if(@value!=nil)
              if(@field.to_s().downcase()=="id")
                @field="sf_id"
              end
              tempHash["#{@field}"]=@value          
            end         
          end                                   
            
          begin  
              if(@id !=nil)   
                sqlUpdate=Sfcontact.find(@id)
                sqlUpdate.update_attributes(tempHash)
                sqlUpdate.save
              else               
                sacct=Sfcontact.new(tempHash)
                sacct.save
                @msg="Succesfully Inserted the records....."
              end
          rescue => e
              logger.error(e)
              id=tempHash["sf_id"]
              puts "Error in inserting data: ", $!, "\n"
              print "ERROR IN INSERTING CASE RECORD:"+e              
              updateErrorTable(e,"Contact","Sfcontact",id) 
              sendEmail(e)                            
          end            
           
        end            
        return @msg
      end 
      
      def updateSolution()
        puts "Updating Solution Object .........."        
        begin
          @sfcol=Solution.columns
          @sqlcol=Sfsolution.columns
          @sfsol=Solution.find(:all, :limit => 5000)
        rescue => e  
          logger.error(e)        
          puts "Error in Querying Solution data: ", $!, "\n"
          print "ERROR IN Querying Solution data:"+e                       
          #sendEmail(e) 
        end      
        
        @sfsol.each do |sfa|                        
          tempHash = Hash.new()
          @id=nil
          @sfcol.each do |acol|            
            @sf_id=sfa.id
            @ifUpdate=Sfsolution.find(:first, :conditions => "sf_id = '#{@sf_id}'")
            if (@ifUpdate)
              @id=@ifUpdate.id
            end
            @field=acol.name 
            #puts " Field............... #{@field}"      
            @value=sfa.send("#{@field}")      
            #puts " Value............... #{@value}"
            
            if(@value!=nil)
              if(@field.to_s().downcase()=="id")
                @field="sf_id"
              end
              tempHash["#{@field}"]=@value          
            end         
          end                                   
            
          begin  
              if(@id !=nil)   
                sqlUpdate=Sfsolution.find(@id)
                sqlUpdate.update_attributes(tempHash)
                sqlUpdate.save
              else                 
                sacct=Sfsolution.new(tempHash)
                sacct.save
                @msg="Succesfully Inserted the records....."
              end
          rescue => e
              logger.error(e)
              id=tempHash["sf_id"]
              puts "Error in inserting data: ", $!, "\n"
              print "ERROR IN INSERTING CASE RECORD:"+e              
              updateErrorTable(e,"Solution","Sfsolution",id) 
              sendEmail(e) 
          end   
        end         
        return @msg
      end 
      
      def updateAttachment()
        puts "Updating Attachemnt .........."
        begin
          @sfcol=Attachment.columns
          @sqlcol=Sfattach.columns
          @sfatt=Attachment.find_all  
          
         
        rescue => e  
          logger.error(e)        
          puts "Error in Querying Attachment data: ", $!, "\n"
          print "ERROR IN Querying Attachment data:"+e                       
          #sendEmail(e) 
        end   
        
        @sfatt.each do |sfa|                  
          tempHash = Hash.new()
          @id=nil
          @sfcol.each do |acol|            
            @sf_id=sfa.id
            @ifUpdate=Sfattach.find(:first, :conditions => "sf_id = '#{@sf_id}'")
            if (@ifUpdate)
              @id=@ifUpdate.id
            end
            @field=acol.name 
            #puts " Field............... #{@field}"      
            @value=sfa.send("#{@field}")      
            #puts " Value............... #{@value}"
            
            if(@value!=nil)
              if(@field.to_s().downcase()=="id")
                @field="sf_id"
              end
              tempHash["#{@field}"]=@value          
            end         
          end                                   
            
          begin  
              if(@id !=nil)   
                sqlUpdate=Sfattach.find(@id)
                sqlUpdate.update_attributes(tempHash)
                sqlUpdate.save
              else               
                sacct=Sfattach.new(tempHash)
                sacct.save
                @msg="Succesfully Inserted the records....."
              end
          rescue => e
            logger.error(e)
            id=tempHash["sf_id"]
            puts "Error in inserting data: ", $!, "\n"
            print "ERROR IN INSERTING CASE RECORD:"+e              
            updateErrorTable(e,"Attachment","Sfattach",id) 
            sendEmail(e) 
          end    
        end            
        return @msg
      end 
      
      def updateErrorTable(errormsg,entity,sqlent,id)
          errorHash=Hash.new()
          if(errormsg !=nil)
            print "DATABASE ERROR:......................"+errormsg
            errorHash["error_message"]=errormsg
            errorHash["sf_id"]=id
            errorHash["sf_entity"]=entity
            errorHash["sql_entity"]=sqlent
            serr=Error.new(errorHash)
            serr.save
          end        
      end
      
      def sendEmail(msg)
        msg = [ "Subject: MySQL database error\n", "\n", msg ]
        Net::SMTP.start('rye.moltenmagma.com') do |smtp|        
          smtp.sendmail( msg,  'ramya@molten-magma.com', ['ramya@molten-magma.com'] )
        end
      end
      
      def updateError()
        puts "Updating Error Object .........."        
        #@sfcol=Solution.columns
        @sfcol=Error.columns
        @sfsol=Error.find(:all, :limit => 50)   
        @sfsol.each do |sfa|                 
          #sacct=Sfaccount.new
          @id=sfa.id
          @sfid=sfa.sf_id
          @sfent=sfa.sf_entity.to_s()
          @sqlent=sfa.sql_entity
                   
          @entCol=eval("#{@sfent}").columns
          
          @sfRec=eval("#{@sfent}").find(:first, :conditions => "id = '#{@sfid}'")
          #@sfRec.each do |ent|
              tempHash = Hash.new()
              @entCol.each do |acol|
                @field=acol.name                 
                puts " Field............... #{@field}"      
                @value=@sfRec.send("#{@field}")      
                
                if(@value!=nil)
                  if(@field.to_s().downcase()=="id")
                    @field="sf_id"
                  end
                  tempHash["#{@field}"]=@value          
                end         
              end 
           #end
          begin         
              sacct=eval("#{@sqlent}").new(tempHash)
              sacct.save
              @msg="Succesfully Inserted the records....."
              Error.delete(@id)
          rescue => e
              logger.error(e)
              id=tempHash["sf_id"]
              puts "Error in inserting data: ", $!, "\n"
              print "ERROR IN INSERTING DATA:"+e              
              updateErrorTable(e,"User","Sfuser",id) 
              sendEmail(e)                     
          end    
        end            
        return @msg
      end  
      
      
      
      def getUpdateAccount()
        puts "Updating last modified Account Object .........."
        begin
          @sfcol=Account.columns
          @sqlcol=Sfaccount.columns
          #@sfusers=User.find(:all, :limit => 1000)  
          #@lastRec=Sfuser.find_by_sql("select last_modified_date from sfuser ORDER BY last_modified_date LIMIT 1")
          @lastRec=Sfaccount.find(:first, :order => "last_modified_date DESC")
          #@ldate=@lastRec.last_modified_date
          if(@lastRec!=nil)
            @ldate=@lastRec.last_modified_date            
          else
            @deflast=Time.now
            @ldate=@deflast-(11*60*60*60)
          end 
          @fromdate=@ldate.strftime("%Y-%m-%dT%H:%M:%SZ") 
          @currentTime=Time.now
          @currentTime=@currentTime+(8*60 * 60)
          @todate=@currentTime.strftime("%Y-%m-%dT%H:%M:%SZ") 
          #puts "LAST MODIFIED DATE is ................................#{@fromdate}"
          #puts "CURRENT MODIFIED DATE is .............................#{@todate}"
          #@sfUpdatedUsers=User.connection.get_updated("User", "#{@fromdate}", "#{@todate}")
          @sfUpdatedAcct=Account.connection.get_updated("Account", "#{@fromdate}", "#{@todate}")
          @queryLen=(@sfUpdatedAcct.length).to_i
          puts "Number of USER records that got updated is #{@queryLen}"
          
        rescue => e  
          logger.error(e)        
          puts "Error in Querying Account data: ", $!, "\n"
          print "ERROR IN Querying Account data:"+e                       
          #sendEmail(e) 
        end   
        if @sfUpdatedAcct !=nil
          @sfUpdatedAcct.each do |sfu|  
            #puts "OBEJCT.......................#{sfu}"
            ids=sfu
            #puts "ID......................#{ids}"
            sfa=Account.find(:first, :conditions => "id = '#{ids}'")         
            tempHash = Hash.new()
            @id=nil
            @sfcol.each do |acol|            
              @sf_id=sfa.id
              @ifUpdate=Sfaccount.find(:first, :conditions => "sf_id = '#{@sf_id}'")
              if (@ifUpdate)
                @id=@ifUpdate.id
              end
              @field=acol.name 
              #puts " Field............... #{@field}"      
              @value=sfa.send("#{@field}")      
              #puts " Value............... #{@value}"
              
              if(@value!=nil)
                if(@field.to_s().downcase()=="id")
                  @field="sf_id"
                end
                tempHash["#{@field}"]=@value          
              end         
            end   
            begin  
                if(@id !=nil)   
                  sqlUpdate=Sfaccount.find(@id)                  
                  sqlUpdate.update_attributes(tempHash)
                  sqlUpdate.save
                else    
                  sacct=Sfaccount.new(tempHash)              
                  sacct.save
                end
                
                @msg="Succesfully Inserted the records....."
            rescue => e
                logger.error(e)
                id=tempHash["sf_id"]
                puts "Error in inserting data: ", $!, "\n"
                print "ERROR IN INSERTING DATA:"+e              
                updateErrorTable(e,"Account","Sfaccount",id) 
                sendEmail(e)                     
            end                
           end  
          end            
          return @msg
      end 
      
      
      def getUpdateCase()
        puts "Updating last modified Case Object .........."
        begin
          @sfcol=Case.columns
          @sqlcol=Sfcase.columns
          #@sfusers=User.find(:all, :limit => 1000)  
          #@lastRec=Sfuser.find_by_sql("select last_modified_date from sfuser ORDER BY last_modified_date LIMIT 1")
          @lastRec=Sfcase.find(:first, :order => "last_modified_date DESC")
          #@ldate=@lastRec.last_modified_date
          if(@lastRec!=nil)
            @ldate=@lastRec.last_modified_date            
          else
            @deflast=Time.now
            @ldate=@deflast-(11*60*60*60)
          end 
          @fromdate=@ldate.strftime("%Y-%m-%dT%H:%M:%SZ") 
          @currentTime=Time.now
          @currentTime=@currentTime+(8*60 * 60)
          @todate=@currentTime.strftime("%Y-%m-%dT%H:%M:%SZ") 
          puts "LAST MODIFIED DATE is ................................#{@fromdate} "
          puts "CURRENT MODIFIED DATE is .............................#{@todate}"
          #@sfUpdatedUsers=User.connection.get_updated("User", "#{@fromdate}", "#{@todate}")
          @sfUpdatedcase=Case.connection.get_updated("Case", "#{@fromdate}", "#{@todate}")
          @queryLen=(@sfUpdatedcase.length).to_i
          puts "Number of Case records that got updated is #{@queryLen}"
          
        rescue => e  
          logger.error(e)        
          puts "Error in Querying Account data: ", $!, "\n"
          print "ERROR IN Querying Account data:"+e                       
          #sendEmail(e) 
        end   
        if @sfUpdatedcase !=nil
          @sfUpdatedcase.each do |sfu|  
            #puts "OBEJCT.......................#{sfu}"
            ids=sfu
            #puts "ID......................#{ids}"
            sfa=Case.find(:first, :conditions => "id = '#{ids}'")         
            tempHash = Hash.new()
            @id=nil
            @sfcol.each do |acol|            
              @sf_id=sfa.id
              @ifUpdate=Sfcase.find(:first, :conditions => "sf_id = '#{@sf_id}'")
              if (@ifUpdate)
                @id=@ifUpdate.id
              end
              @field=acol.name 
              #puts " Field............... #{@field}"      
              @value=sfa.send("#{@field}")      
              #puts " Value............... #{@value}"
              
              if(@value!=nil)
                if(@field.to_s().downcase()=="id")
                  @field="sf_id"
                end
                tempHash["#{@field}"]=@value          
              end         
            end   
            begin  
                if(@id !=nil)   
                  sqlUpdate=Sfcase.find(@id)                  
                  sqlUpdate.update_attributes(tempHash)
                  sqlUpdate.save
                else    
                  sacct=Sfcase.new(tempHash)              
                  sacct.save
                end
                
                @msg="Succesfully Inserted the records....."
            rescue => e
                logger.error(e)
                id=tempHash["sf_id"]
                puts "Error in inserting data: ", $!, "\n"
                print "ERROR IN INSERTING DATA:"+e              
                updateErrorTable(e,"Case","Sfcase",id) 
                sendEmail(e)                     
            end                
           end  
          end            
          return @msg
      end 
      
      
      
      def getUpdateUser()
        puts "Updating last modified User Object .........."
        begin
          @sfcol=User.columns
          @sqlcol=Sfuser.columns
          #@sfusers=User.find(:all, :limit => 1000)  
          #@lastRec=Sfuser.find_by_sql("select last_modified_date from sfuser ORDER BY last_modified_date LIMIT 1")
          @lastRec=Sfuser.find(:first, :order => "last_modified_date DESC")
          #@ldate=@lastRec.last_modified_date
          if(@lastRec!=nil)
            @ldate=@lastRec.last_modified_date            
          else
            @deflast=Time.now
            @ldate=@deflast-(11*60*60*60)
          end 
          @fromdate=@ldate.strftime("%Y-%m-%dT%H:%M:%SZ") 
          @currentTime=Time.now
          @currentTime=@currentTime+(8*60 * 60)
          @todate=@currentTime.strftime("%Y-%m-%dT%H:%M:%SZ") 
          puts "LAST MODIFIED DATE is ................................#{@fromdate}"
          puts "CURRENT MODIFIED DATE is .............................#{@todate}"
          #@sfUpdatedUsers=User.connection.get_updated("User", "#{@fromdate}", "#{@todate}")
          @sfUpdatedUsers=User.connection.get_updated("User", "#{@fromdate}", "#{@todate}")
          @queryLen=(@sfUpdatedUsers.length).to_i
          puts "Number of USER records that got updated is #{@queryLen}"
          
        rescue => e  
          logger.error(e)        
          puts "Error in Querying User data: ", $!, "\n"
          print "ERROR IN Querying User data:"+e                       
          #sendEmail(e) 
        end   
        if @sfUpdatedUsers !=nil
          @sfUpdatedUsers.each do |sfu|  
            #puts "OBEJCT.......................#{sfu}"
            ids=sfu
            #puts "ID......................#{ids}"
            sfa=User.find(:first, :conditions => "id = '#{ids}'")         
            tempHash = Hash.new()
            @id=nil
            @sfcol.each do |acol|            
              @sf_id=sfa.id
              @ifUpdate=Sfuser.find(:first, :conditions => "sf_id = '#{@sf_id}'")
              if (@ifUpdate)
                @id=@ifUpdate.id
              end
              @field=acol.name 
              #puts " Field............... #{@field}"      
              @value=sfa.send("#{@field}")      
              #puts " Value............... #{@value}"
              
              if(@value!=nil)
                if(@field.to_s().downcase()=="id")
                  @field="sf_id"
                end
                tempHash["#{@field}"]=@value          
              end         
            end   
            begin  
                if(@id !=nil)   
                  sqlUpdate=Sfuser.find(@id)                  
                  sqlUpdate.update_attributes(tempHash)
                  sqlUpdate.save
                else    
                  sacct=Sfuser.new(tempHash)              
                  sacct.save
                end
                
                @msg="Succesfully Inserted the records....."
            rescue => e
                logger.error(e)
                id=tempHash["sf_id"]
                puts "Error in inserting data: ", $!, "\n"
                print "ERROR IN INSERTING DATA:"+e              
                updateErrorTable(e,"User","Sfuser",id) 
                sendEmail(e)                     
            end                
           end  
          end            
          return @msg
      end 
      
      
      def getUpdateSSL()
        puts "Updating last modified Case Object .........."
        begin
          @sfcol=SelfServiceUser.columns
          @sqlcol=Sfssl.columns
          #@sfusers=User.find(:all, :limit => 1000)  
          #@lastRec=Sfuser.find_by_sql("select last_modified_date from sfuser ORDER BY last_modified_date LIMIT 1")
          @lastRec=Sfssl.find(:first, :order => "last_modified_date DESC")
          #@ldate=@lastRec.last_modified_date
          if(@lastRec!=nil)
            @ldate=@lastRec.last_modified_date            
          else
            @deflast=Time.now
            @ldate=@deflast-(11*60*60*60)
          end 
          @fromdate=@ldate.strftime("%Y-%m-%dT%H:%M:%SZ") 
          @currentTime=Time.now
          @currentTime=@currentTime+(8*60 * 60)
          @todate=@currentTime.strftime("%Y-%m-%dT%H:%M:%SZ") 
          puts "LAST MODIFIED DATE is ................................#{@fromdate} "
          puts "CURRENT MODIFIED DATE is .............................#{@todate}"
          #@sfUpdatedUsers=User.connection.get_updated("User", "#{@fromdate}", "#{@todate}")
          @sfUpdatedssl=SelfServiceUser.connection.get_updated("SelfServiceUser", "#{@fromdate}", "#{@todate}")
          @queryLen=(@sfUpdatedssl.length).to_i
          puts "Number of SelfServiceUser records that got updated is #{@queryLen}"
          
        rescue => e  
          logger.error(e)        
          puts "Error in Querying SelfServiceUser data: ", $!, "\n"
          print "ERROR IN Querying SelfServiceUser data:"+e                       
          #sendEmail(e) 
        end   
        if @sfUpdatedssl !=nil
          @sfUpdatedssl.each do |sfu|  
            #puts "OBEJCT.......................#{sfu}"
            ids=sfu
            #puts "ID......................#{ids}"
            sfa=SelfServiceUser.find(:first, :conditions => "id = '#{ids}'")         
            tempHash = Hash.new()
            @id=nil
            @sfcol.each do |acol|            
              @sf_id=sfa.id
              @ifUpdate=Sfssl.find(:first, :conditions => "sf_id = '#{@sf_id}'")
              if (@ifUpdate)
                @id=@ifUpdate.id
              end
              @field=acol.name 
              #puts " Field............... #{@field}"      
              @value=sfa.send("#{@field}")      
              #puts " Value............... #{@value}"
              
              if(@value!=nil)
                if(@field.to_s().downcase()=="id")
                  @field="sf_id"
                end
                tempHash["#{@field}"]=@value          
              end         
            end   
            begin  
                if(@id !=nil)   
                  sqlUpdate=Sfssl.find(@id)                  
                  sqlUpdate.update_attributes(tempHash)
                  sqlUpdate.save
                else    
                  sacct=Sfcase.new(tempHash)              
                  sacct.save
                end
                
                @msg="Succesfully Inserted the records....."
            rescue => e
                logger.error(e)
                id=tempHash["sf_id"]
                puts "Error in inserting data: ", $!, "\n"
                print "ERROR IN INSERTING DATA:"+e              
                updateErrorTable(e,"SelfServiceUser","Sfssl",id) 
                sendEmail(e)                     
            end                
           end  
          end            
          return @msg
      end 
      
      
      
      def getUpdateContact()
        puts "Updating last modified Case Object .........."
        begin
          @sfcol=Contact.columns
          @sqlcol=Sfcontact.columns
          #@sfusers=User.find(:all, :limit => 1000)  
          #@lastRec=Sfuser.find_by_sql("select last_modified_date from sfuser ORDER BY last_modified_date LIMIT 1")
          @lastRec=Sfcontact.find(:first, :order => "last_modified_date DESC")
          puts "LAST RECORS LENGTH ---------------------#{@lastRec}"
          if(@lastRec!=nil)
            @ldate=@lastRec.last_modified_date            
          else
            @deflast=Time.now
            @ldate=@deflast-(11*60*60*60)
          end  
          @fromdate=@ldate.strftime("%Y-%m-%dT%H:%M:%SZ") 
          @currentTime=Time.now
          @currentTime=@currentTime+(8*60 * 60)
          @todate=@currentTime.strftime("%Y-%m-%dT%H:%M:%SZ") 
          puts "LAST MODIFIED DATE is ................................#{@fromdate}"
          puts "CURRENT MODIFIED DATE is .............................#{@todate}"
          #@sfUpdatedUsers=User.connection.get_updated("User", "#{@fromdate}", "#{@todate}")
          @sfUpdatedcont=Contact.connection.get_updated("Contact", "#{@fromdate}", "#{@todate}")
          @queryLen=(@sfUpdatedcont.length).to_i
          puts "Number of Contact records that got updated is #{@queryLen}"
          
        rescue => e  
          logger.error(e)        
          puts "Error in Querying Contact data: ", $!, "\n"
          print "ERROR IN Querying Contact data:"+e                       
          #sendEmail(e) 
        end   
        if @sfUpdatedcont !=nil
          @sfUpdatedcont.each do |sfu|  
            #puts "OBEJCT.......................#{sfu}"
            ids=sfu
            #puts "ID......................#{ids}"
            sfa=Contact.find(:first, :conditions => "id = '#{ids}'")         
            tempHash = Hash.new()
            @id=nil
            @sfcol.each do |acol|            
              @sf_id=sfa.id
              @ifUpdate=Sfcontact.find(:first, :conditions => "sf_id = '#{@sf_id}'")
              if (@ifUpdate)
                @id=@ifUpdate.id
              end
              @field=acol.name 
              #puts " Field............... #{@field}"      
              @value=sfa.send("#{@field}")      
              #puts " Value............... #{@value}"
              
              if(@value!=nil)
                if(@field.to_s().downcase()=="id")
                  @field="sf_id"
                end
                tempHash["#{@field}"]=@value          
              end         
            end   
            begin  
                if(@id !=nil)   
                  sqlUpdate=Sfcontact.find(@id)                  
                  sqlUpdate.update_attributes(tempHash)
                  sqlUpdate.save
                else    
                  sacct=Sfcontact.new(tempHash)              
                  sacct.save
                end
                
                @msg="Succesfully Inserted the records....."
            rescue => e
                logger.error(e)
                id=tempHash["sf_id"]
                puts "Error in inserting data: ", $!, "\n"
                print "ERROR IN INSERTING DATA:"+e              
                updateErrorTable(e,"Contact","Sfcontact",id) 
                sendEmail(e)                     
            end                
           end  
          end            
          return @msg
      end 
      
      def getUpdateSolution()
        puts "Updating last modified Case Object .........."
        begin
          @sfcol=Solution.columns
          @sqlcol=Sfsolution.columns
          #@sfusers=User.find(:all, :limit => 1000)  
          #@lastRec=Sfuser.find_by_sql("select last_modified_date from sfuser ORDER BY last_modified_date LIMIT 1")
          @lastRec=Sfsolution.find(:first, :order => "last_modified_date DESC")
          #@ldate=@lastRec.last_modified_date
          if(@lastRec!=nil)
            @ldate=@lastRec.last_modified_date            
          else
            @deflast=Time.now
            @ldate=@deflast-(11*60*60*60)
          end 
          @fromdate=@ldate.strftime("%Y-%m-%dT%H:%M:%SZ") 
          @currentTime=Time.now
          @currentTime=@currentTime+(8*60 * 60)
          @todate=@currentTime.strftime("%Y-%m-%dT%H:%M:%SZ") 
          puts "LAST MODIFIED DATE is ................................#{@fromdate} "
          puts "CURRENT MODIFIED DATE is .............................#{@todate}"
          #@sfUpdatedUsers=User.connection.get_updated("User", "#{@fromdate}", "#{@todate}")
          @sfUpdatedsol=Solution.connection.get_updated("Solution", "#{@fromdate}", "#{@todate}")
          @queryLen=(@sfUpdatedsol.length).to_i
          puts "Number of Solution records that got updated is #{@queryLen}"
          
        rescue => e  
          logger.error(e)        
          puts "Error in Querying Solution data: ", $!, "\n"
          print "ERROR IN Querying Solution data:"+e                       
          #sendEmail(e) 
        end   
        if @sfUpdatedsol !=nil
          @sfUpdatedsol.each do |sfu|  
            #puts "OBEJCT.......................#{sfu}"
            ids=sfu
            #puts "ID......................#{ids}"
            sfa=Solution.find(:first, :conditions => "id = '#{ids}'")         
            tempHash = Hash.new()
            @id=nil
            @sfcol.each do |acol|            
              @sf_id=sfa.id
              @ifUpdate=Sfsolution.find(:first, :conditions => "sf_id = '#{@sf_id}'")
              if (@ifUpdate)
                @id=@ifUpdate.id
              end
              @field=acol.name 
              #puts " Field............... #{@field}"      
              @value=sfa.send("#{@field}")      
              #puts " Value............... #{@value}"
              
              if(@value!=nil)
                if(@field.to_s().downcase()=="id")
                  @field="sf_id"
                end
                tempHash["#{@field}"]=@value          
              end         
            end   
            begin  
                if(@id !=nil)   
                  sqlUpdate=Sfsolution.find(@id)                  
                  sqlUpdate.update_attributes(tempHash)
                  sqlUpdate.save
                else    
                  sacct=Sfsolution.new(tempHash)              
                  sacct.save
                end
                
                @msg="Succesfully Inserted the records....."
            rescue => e
                logger.error(e)
                id=tempHash["sf_id"]
                puts "Error in inserting data: ", $!, "\n"
                print "ERROR IN INSERTING DATA:"+e              
                updateErrorTable(e,"Solution","Sfsolution",id) 
                sendEmail(e)                     
            end                
           end  
          end            
          return @msg
      end 
      
      
      def getUpdateAttachment()
        puts "Updating last modified Case Object .........."
        begin
          @sfcol=Attachment.columns
          @sqlcol=Sfattach.columns
          #@sfusers=User.find(:all, :limit => 1000)  
          #@lastRec=Sfuser.find_by_sql("select last_modified_date from sfuser ORDER BY last_modified_date LIMIT 1")
          @lastRec=Sfattach.find(:first, :order => "last_modified_date DESC")
          #@ldate=@lastRec.last_modified_date
          if(@lastRec!=nil)
            @ldate=@lastRec.last_modified_date            
          else
            @deflast=Time.now
            @ldate=@deflast-(11*60*60*60)
          end 
          @fromdate=@ldate.strftime("%Y-%m-%dT%H:%M:%SZ") 
          @currentTime=Time.now
          @currentTime=@currentTime+(8*60 * 60)
          @todate=@currentTime.strftime("%Y-%m-%dT%H:%M:%SZ") 
          puts "LAST MODIFIED DATE is ................................#{@fromdate}"
          puts "CURRENT MODIFIED DATE is .............................#{@todate}"
          #@sfUpdatedUsers=User.connection.get_updated("User", "#{@fromdate}", "#{@todate}")
          @sfUpdatedattach=Attachment.connection.get_updated("Attachment", "#{@fromdate}", "#{@todate}")
          @queryLen=(@sfUpdatedattach.length).to_i
          puts "Number of Solution records that got updated is #{@queryLen}"
          
        rescue => e  
          logger.error(e)        
          puts "Error in Querying Attachment data: ", $!, "\n"
          print "ERROR IN Querying Attachment data:"+e                       
          #sendEmail(e) 
        end   
        if @sfUpdatedattach !=nil
          @sfUpdatedattach.each do |sfu|  
            #puts "OBEJCT.......................#{sfu}"
            ids=sfu
            #puts "ID......................#{ids}"
            sfa=Attachment.find(:first, :conditions => "id = '#{ids}'")         
            tempHash = Hash.new()
            @id=nil
            @sfcol.each do |acol|            
              @sf_id=sfa.id
              @ifUpdate=Sfattach.find(:first, :conditions => "sf_id = '#{@sf_id}'")
              if (@ifUpdate)
                @id=@ifUpdate.id
              end
              @field=acol.name 
              #puts " Field............... #{@field}"      
              @value=sfa.send("#{@field}")      
              #puts " Value............... #{@value}"
              
              if(@value!=nil)
                if(@field.to_s().downcase()=="id")
                  @field="sf_id"
                end
                tempHash["#{@field}"]=@value          
              end         
            end   
            begin  
                if(@id !=nil)   
                  sqlUpdate=Sfattach.find(@id)                  
                  sqlUpdate.update_attributes(tempHash)
                  sqlUpdate.save
                else    
                  sacct=Sfattach.new(tempHash)              
                  sacct.save
                end
                
                @msg="Succesfully Inserted the records....."
            rescue => e
                logger.error(e)
                id=tempHash["sf_id"]
                puts "Error in inserting data: ", $!, "\n"
                print "ERROR IN INSERTING DATA:"+e              
                updateErrorTable(e,"Attachment","Sfattach",id) 
                sendEmail(e)                     
            end                
           end  
          end            
          return @msg
      end 
        
end