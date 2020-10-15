require 'rubygems'

class SfSchemaUpdater < ActiveRecord::Migration

  #@allaccounts=Account.find_all
  @acctColumns=Account.columns
  @sqlaccount=Sfaccount.columns
  
  @userColumns=User.columns
  @sqlUser=Sfuser.columns
  
  @sslColumns=SelfServiceUser.columns
  @sqlSsl=Sfssl.columns
  
  @caseColumns=Case.columns
  @sqlCase=Sfcase.columns
  
  @contColumns=Contact.columns
  @sqlContact=Sfcontact.columns
  
  @solColumns=Solution.columns
  @sqlSol=Sfsolution.columns
  
  @attachColumns=Attachment.columns
  @sqlAttach=Sfattach.columns
  
 
  
  def self.up
   
    @acctColumns.each do |acol|
        @colname=acol.name
        #puts "SF COLUMNS...#{@colname}"
        colexist="False"
        @sqlaccount.each do |sfacctcol|
          sqlacol=sfacctcol.name
          #puts "SF COLUMNS...#{@colname}.....#{sqlacol}"
          if(sqlacol.to_s().downcase() == @colname.to_s().downcase())
            colexist="True"
            #puts  "SF COLUMNS...#{@colname}.....#{sqlacol}"
          end
        end
        #puts "Column Exist .....#{colexist}"
        if (colexist.to_s()=="False")
          #puts "Inserting column..... #{@colname}"
          add_column "sfaccount", "#{@colname}",:string
        end
    end
    
    @userColumns.each do |acol|
        @colname=acol.name
        #puts "SF COLUMNS...#{@colname}"
        colexist="False"
        @sqlUser.each do |sfacctcol|
          sqlacol=sfacctcol.name
          #puts "SF COLUMNS...#{@colname}.....#{sqlacol}"
          if(sqlacol.to_s().downcase() == @colname.to_s().downcase())
            colexist="True"
            #puts  "SF COLUMNS...#{@colname}.....#{sqlacol}"
          end
        end
        #puts "Column Exist .....#{colexist}"
        if (colexist.to_s()=="False")
          #puts "Inserting column..... #{@colname}"
          add_column "sfuser", "#{@colname}",:string
        end
    end
    
    @sslColumns.each do |acol|
        @colname=acol.name
        #puts "SF COLUMNS...#{@colname}"
        colexist="False"
        @sqlSsl.each do |sfacctcol|
          sqlacol=sfacctcol.name
          #puts "SF COLUMNS...#{@colname}.....#{sqlacol}"
          if(sqlacol.to_s().downcase() == @colname.to_s().downcase())
            colexist="True"
            #puts  "SF COLUMNS...#{@colname}.....#{sqlacol}"
          end
        end
        #puts "Column Exist .....#{colexist}"
        if (colexist.to_s()=="False")
          #puts "Inserting column..... #{@colname}"
          add_column "sfssl", "#{@colname}",:string
        end
    end
    
    @caseColumns.each do |acol|
        @colname=acol.name
        #puts "SF COLUMNS...#{@colname}"
        colexist="False"
        @sqlCase.each do |sfacctcol|
          sqlacol=sfacctcol.name
          #puts "SF COLUMNS...#{@colname}.....#{sqlacol}"
          if(sqlacol.to_s().downcase() == @colname.to_s().downcase())
            colexist="True"
            #puts  "SF COLUMNS...#{@colname}.....#{sqlacol}"
          end
        end
        #puts "Column Exist .....#{colexist}"
        if (colexist.to_s()=="False")
          #puts "Inserting column..... #{@colname}"
          add_column "sfcase", "#{@colname}",:string
        end
    end
    
    @contColumns.each do |acol|
        @colname=acol.name
        #puts "SF COLUMNS...#{@colname}"
        colexist="False"
        @sqlContact.each do |sfacctcol|
          sqlacol=sfacctcol.name
          #puts "SF COLUMNS...#{@colname}.....#{sqlacol}"
          if(sqlacol.to_s().downcase() == @colname.to_s().downcase())
            colexist="True"
            #puts  "SF COLUMNS...#{@colname}.....#{sqlacol}"
          end
        end
        #puts "Column Exist .....#{colexist}"
        if (colexist.to_s()=="False")
          #puts "Inserting column..... #{@colname}"
          add_column "sfcontact", "#{@colname}",:string
        end
    end
    
    @solColumns.each do |acol|
        @colname=acol.name
        #puts "SF COLUMNS...#{@colname}"
        colexist="False"
        @sqlSol.each do |sfacctcol|
          sqlacol=sfacctcol.name
          #puts "SF COLUMNS...#{@colname}.....#{sqlacol}"
          if(sqlacol.to_s().downcase() == @colname.to_s().downcase())
            colexist="True"
            #puts  "SF COLUMNS...#{@colname}.....#{sqlacol}"
          end
        end
        #puts "Column Exist .....#{colexist}"
        if (colexist.to_s()=="False")
          #puts "Inserting column..... #{@colname}"
          add_column "sfsolution", "#{@colname}",:string
        end
    end
    
    @attachColumns.each do |acol|
        @colname=acol.name
        #puts "SF COLUMNS...#{@colname}"
        colexist="False"
        @sqlAttach.each do |sfacctcol|
          sqlacol=sfacctcol.name
          #puts "SF COLUMNS...#{@colname}.....#{sqlacol}"
          if(sqlacol.to_s().downcase() == @colname.to_s().downcase())
            colexist="True"
            #puts  "SF COLUMNS...#{@colname}.....#{sqlacol}"
          end
        end
        #puts "Column Exist .....#{colexist}"
        if (colexist.to_s()=="False")
          #puts "Inserting column..... #{@colname}"
          add_column "sfattach", "#{@colname}",:string
        end
    end
    
       
  end

  def self.down
  end
end
