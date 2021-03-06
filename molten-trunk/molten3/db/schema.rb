# This file is autogenerated. Instead of editing this file, please use the
# migrations feature of ActiveRecord to incrementally modify your database, and
# then regenerate this schema definition.

ActiveRecord::Schema.define(:version => 4) do

  create_table "error", :force => true do |t|
    t.column "sf_id", :string
    t.column "sf_entity", :string
    t.column "sql_entity", :string
    t.column "error_message", :text
    t.column "created_time", :datetime
    t.column "other_information", :text
    t.column "last_modified", :datetime
  end

  create_table "sfaccount", :force => true do |t|
    t.column "name", :string, :default => "", :null => false
    t.column "type", :string, :default => "", :null => false
    t.column "parent_id", :string, :default => "", :null => false
    t.column "billing_street", :string, :default => "", :null => false
    t.column "billing_city", :string, :default => "", :null => false
    t.column "billing_state", :string, :default => "", :null => false
    t.column "billing_postal_code", :string, :default => "", :null => false
    t.column "billing_country", :string, :default => "", :null => false
    t.column "shipping_street", :string, :default => "", :null => false
    t.column "shipping_city", :string, :default => "", :null => false
    t.column "shipping_state", :string, :default => "", :null => false
    t.column "shipping_postal_code", :string, :default => "", :null => false
    t.column "shipping_country", :string, :default => "", :null => false
    t.column "phone", :string, :default => "", :null => false
    t.column "fax", :string, :default => "", :null => false
    t.column "website", :string, :default => "", :null => false
    t.column "description", :string, :default => "", :null => false
    t.column "site", :string, :default => "", :null => false
    t.column "owner_id", :string, :default => "", :null => false
    t.column "created_date", :datetime, :null => false
    t.column "created_by_id", :string, :default => "", :null => false
    t.column "last_modified_date", :datetime, :null => false
    t.column "last_modified_by_id", :string, :default => "", :null => false
    t.column "system_modstamp", :datetime, :null => false
    t.column "host_id__c", :string, :default => "", :null => false
    t.column "sales_region__c", :string, :default => "", :null => false
    t.column "dun_snumber__c", :string, :default => "", :null => false
    t.column "tam_front_end_seats__c", :string, :default => "", :null => false
    t.column "tam_back_end_seats__c", :string, :default => "", :null => false
    t.column "customer_id__c", :string, :default => "", :null => false
    t.column "address_issue__c", :string, :default => "", :null => false
    t.column "credit_rating__c", :string, :default => "", :null => false
    t.column "nda__c", :string, :default => "", :null => false
    t.column "nda_description__c", :string, :default => "", :null => false
    t.column "customer_support_alias__c", :string, :default => "", :null => false
    t.column "sap_sync_status__c", :string, :default => "", :null => false
    t.column "sap_payment_terms__c", :string, :default => "", :null => false
    t.column "sap_account_group__c", :string, :default => "", :null => false
    t.column "lead_ae_email__c", :string, :default => "", :null => false
    t.column "sap_sales_districts__c", :string, :default => "", :null => false
    t.column "sap_customer_id__c", :string, :default => "", :null => false
    t.column "tsmc_lib_nda_front_end__c", :string, :default => "", :null => false
    t.column "sap_legacy_id__c", :string, :default => "", :null => false
    t.column "sla__c", :string, :default => "", :null => false
    t.column "initial_sap_upload__c", :string, :default => "", :null => false
    t.column "nda_expiration_date__c", :date, :null => false
    t.column "tsmc_lib_nda_complete__c", :string, :default => "", :null => false
    t.column "credit_score__c", :string, :default => "", :null => false
    t.column "entity_type__c", :string, :default => "", :null => false
    t.column "credit_score_updated__c", :date, :null => false
    t.column "activities__c", :string, :default => "", :null => false
    t.column "dns_domain__c", :string, :default => "", :null => false
    t.column "allow_molten__c", :string, :default => "", :null => false
    t.column "toll_free_phone__c", :string, :default => "", :null => false
    t.column "account_type_code__c", :string, :default => "", :null => false
    t.column "sap_org_id__c", :string, :default => "", :null => false
    t.column "sf_id", :string, :default => "", :null => false
  end

  create_table "sfattach", :force => true do |t|
    t.column "parent_id", :string, :default => "", :null => false
    t.column "name", :string, :default => "", :null => false
    t.column "is_private", :string, :default => "", :null => false
    t.column "content_type", :string, :default => "", :null => false
    t.column "body_length", :integer, :default => 0, :null => false
    t.column "body", :string, :default => "", :null => false
    t.column "owner_id", :string, :default => "", :null => false
    t.column "created_date", :datetime, :null => false
    t.column "created_by_id", :string, :default => "", :null => false
    t.column "last_modified_date", :datetime, :null => false
    t.column "last_modified_by_id", :string, :default => "", :null => false
    t.column "system_modstamp", :datetime, :null => false
    t.column "sf_id", :string, :default => "", :null => false
  end

  create_table "sfcase", :force => true do |t|
    t.column "case_number", :string, :default => "", :null => false
    t.column "contact_id", :string, :default => "", :null => false
    t.column "asset_id", :string, :default => "", :null => false
    t.column "supplied_name", :string, :default => "", :null => false
    t.column "supplied_email", :string, :default => "", :null => false
    t.column "supplied_phone", :string, :default => "", :null => false
    t.column "supplied_company", :string, :default => "", :null => false
    t.column "type", :string, :default => "", :null => false
    t.column "record_type_id", :string, :default => "", :null => false
    t.column "status", :string, :default => "", :null => false
    t.column "origin", :string, :default => "", :null => false
    t.column "is_visible_in_css", :string, :default => "", :null => false
    t.column "subject", :string, :default => "", :null => false
    t.column "priority", :string, :default => "", :null => false
    t.column "description", :string, :default => "", :null => false
    t.column "is_closed", :string, :default => "", :null => false
    t.column "closed_date", :datetime, :null => false
    t.column "is_escalated", :string, :default => "", :null => false
    t.column "owner_id", :string, :default => "", :null => false
    t.column "created_date", :datetime, :null => false
    t.column "created_by_id", :string, :default => "", :null => false
    t.column "last_modified_date", :datetime, :null => false
    t.column "last_modified_by_id", :string, :default => "", :null => false
    t.column "system_modstamp", :datetime, :null => false
    t.column "quart_formal__c", :string, :default => "", :null => false
    t.column "clarify_id__c", :string, :default => "", :null => false
    t.column "originator__c", :string, :default => "", :null => false
    t.column "customer_priority__c", :string, :default => "", :null => false
    t.column "operating_system__c", :string, :default => "", :null => false
    t.column "reproducible__c", :string, :default => "", :null => false
    t.column "component__c", :string, :default => "", :null => false
    t.column "customer_tracking__c", :string, :default => "", :null => false
    t.column "query_build_view__c", :string, :default => "", :null => false
    t.column "dataor_test_case_provided__c", :string, :default => "", :null => false
    t.column "design_geometryn_m__c", :string, :default => "", :null => false
    t.column "foundry__c", :string, :default => "", :null => false
    t.column "cell_count_k_objects__c", :string, :default => "", :null => false
    t.column "speed_m_hz__c", :string, :default => "", :null => false
    t.column "scopeof_flow__c", :string, :default => "", :null => false
    t.column "formal_verification__c", :string, :default => "", :null => false
    t.column "qualityof_results__c", :string, :default => "", :null => false
    t.column "hdl__c", :string, :default => "", :null => false
    t.column "test_case_path__c", :string, :default => "", :null => false
    t.column "std_cell_library__c", :string, :default => "", :null => false
    t.column "tape_out_date__c", :date, :null => false
    t.column "synthesis_tool__c", :string, :default => "", :null => false
    t.column "schedule_status__c", :string, :default => "", :null => false
    t.column "time_stamp_build__c", :string, :default => "", :null => false
    t.column "version_number__c", :string, :default => "", :null => false
    t.column "noise_signoff__c", :string, :default => "", :null => false
    t.column "power_signoff__c", :string, :default => "", :null => false
    t.column "clarify_customer__c", :string, :default => "", :null => false
    t.column "blast_power__c", :string, :default => "", :null => false
    t.column "analysis_tool__c", :string, :default => "", :null => false
    t.column "target_release__c", :string, :default => "", :null => false
    t.column "clarify_create_date__c", :date, :null => false
    t.column "program_area__c", :string, :default => "", :null => false
    t.column "expedited_priority__c", :string, :default => "", :null => false
    t.column "target_fast_track_build__c", :date, :null => false
    t.column "estimated_start_date__c", :date, :null => false
    t.column "estimated_finish_date__c", :date, :null => false
    t.column "test_case_provided__c", :string, :default => "", :null => false
    t.column "customer_visible__c", :string, :default => "", :null => false
    t.column "opportunity_name__c", :string, :default => "", :null => false
    t.column "requested_start_date__c", :date, :null => false
    t.column "requested_end_date__c", :date, :null => false
    t.column "initial_quality_of_results__c", :string, :default => "", :null => false
    t.column "initial_util__c", :float, :default => 0.0, :null => false
    t.column "palace_options_used__c", :string, :default => "", :null => false
    t.column "initial_speed__c", :string, :default => "", :null => false
    t.column "design_top_level_name__c", :string, :default => "", :null => false
    t.column "mode__c", :string, :default => "", :null => false
    t.column "number_of_clocks__c", :string, :default => "", :null => false
    t.column "number_of_design_blocks__c", :string, :default => "", :null => false
    t.column "power_analysis_tool__c", :string, :default => "", :null => false
    t.column "tape_out_limiting__c", :string, :default => "", :null => false
    t.column "sales_opportunity_related__c", :string, :default => "", :null => false
    t.column "benmark_impacted__c", :string, :default => "", :null => false
    t.column "special_situation__c", :string, :default => "", :null => false
    t.column "special_situation_desc__c", :string, :default => "", :null => false
    t.column "benchmark_case__c", :string, :default => "", :null => false
    t.column "product__c", :string, :default => "", :null => false
    t.column "is_closeable__c", :string, :default => "", :null => false
    t.column "schedule_comments__c", :string, :default => "", :null => false
    t.column "shadow_status__c", :string, :default => "", :null => false
    t.column "code_streams_priority__c", :string, :default => "", :null => false
    t.column "tag__c", :string, :default => "", :null => false
    t.column "blast_fusion__c", :string, :default => "", :null => false
    t.column "blast_logic__c", :string, :default => "", :null => false
    t.column "blast_fusion_apx__c", :string, :default => "", :null => false
    t.column "blast_noise__c", :string, :default => "", :null => false
    t.column "blast_plan__c", :string, :default => "", :null => false
    t.column "blast_plan_pro__c", :string, :default => "", :null => false
    t.column "blast_rail__c", :string, :default => "", :null => false
    t.column "blast_rtl__c", :string, :default => "", :null => false
    t.column "engineer_assigned__c", :string, :default => "", :null => false
    t.column "logic_verification__c", :string, :default => "", :null => false
    t.column "physical_verification__c", :string, :default => "", :null => false
    t.column "extraction__c", :string, :default => "", :null => false
    t.column "timing_signoff__c", :string, :default => "", :null => false
    t.column "dft__c", :string, :default => "", :null => false
    t.column "expected_build_date__c", :date, :null => false
    t.column "blast_create__c", :string, :default => "", :null => false
    t.column "man_hours_of_effort__c", :string, :default => "", :null => false
    t.column "workaround_description__c", :string, :default => "", :null => false
    t.column "workaround_available__c", :string, :default => "", :null => false
    t.column "needs_docs__c", :string, :default => "", :null => false
    t.column "target_releases__c", :string, :default => "", :null => false
    t.column "expected_resolution_date__c", :date, :null => false
    t.column "fix_version__c", :string, :default => "", :null => false
    t.column "cr_list_id__c", :string, :default => "", :null => false
    t.column "crash_details__c", :string, :default => "", :null => false
    t.column "description_notes__c", :string, :default => "", :null => false
    t.column "tech_campaign_id__c", :string, :default => "", :null => false
    t.column "release_note__c", :string, :default => "", :null => false
    t.column "tech_campaign2_id__c", :string, :default => "", :null => false
    t.column "r_d_submission__c", :string, :default => "", :null => false
    t.column "pe_owner_user_id__c", :string, :default => "", :null => false
    t.column "component_link_id__c", :string, :default => "", :null => false
    t.column "aging_weeks__c", :string, :default => "", :null => false
    t.column "internal_comments__c", :string, :default => "", :null => false
    t.column "committed__c", :string, :default => "", :null => false
    t.column "level_of_effort__c", :float, :default => 0.0, :null => false
    t.column "sf_id", :string, :default => "", :null => false
  end

  create_table "sfcontact", :force => true do |t|
    t.column "account_id", :string, :default => "", :null => false
    t.column "last_name", :string, :default => "", :null => false
    t.column "first_name", :string, :default => "", :null => false
    t.column "salutation", :string, :default => "", :null => false
    t.column "record_type_id", :string, :default => "", :null => false
    t.column "other_street", :string, :default => "", :null => false
    t.column "other_city", :string, :default => "", :null => false
    t.column "other_state", :string, :default => "", :null => false
    t.column "other_postal_code", :string, :default => "", :null => false
    t.column "other_country", :string, :default => "", :null => false
    t.column "mailing_street", :string, :default => "", :null => false
    t.column "mailing_city", :string, :default => "", :null => false
    t.column "mailing_state", :string, :default => "", :null => false
    t.column "mailing_postal_code", :string, :default => "", :null => false
    t.column "mailing_country", :string, :default => "", :null => false
    t.column "phone", :string, :default => "", :null => false
    t.column "fax", :string, :default => "", :null => false
    t.column "mobile_phone", :string, :default => "", :null => false
    t.column "home_phone", :string, :default => "", :null => false
    t.column "other_phone", :string, :default => "", :null => false
    t.column "assistant_phone", :string, :default => "", :null => false
    t.column "reports_to_id", :string, :default => "", :null => false
    t.column "email", :string, :default => "", :null => false
    t.column "title", :string, :default => "", :null => false
    t.column "department", :string, :default => "", :null => false
    t.column "assistant_name", :string, :default => "", :null => false
    t.column "lead_source", :string, :default => "", :null => false
    t.column "birthdate", :date, :null => false
    t.column "description", :string, :default => "", :null => false
    t.column "owner_id", :string, :default => "", :null => false
    t.column "has_opted_out_of_email", :string, :default => "", :null => false
    t.column "created_date", :datetime, :null => false
    t.column "created_by_id", :string, :default => "", :null => false
    t.column "last_modified_date", :datetime, :null => false
    t.column "last_modified_by_id", :string, :default => "", :null => false
    t.column "system_modstamp", :datetime, :null => false
    t.column "last_cu_request_date", :datetime, :null => false
    t.column "last_cu_update_date", :datetime, :null => false
    t.column "portal_password__c", :string, :default => "", :null => false
    t.column "magma_user__c", :string, :default => "", :null => false
    t.column "contact_status__c", :string, :default => "", :null => false
    t.column "personal_invite_only__c", :string, :default => "", :null => false
    t.column "product_group__c", :string, :default => "", :null => false
    t.column "notification_frequency__c", :string, :default => "", :null => false
    t.column "mail_stop__c", :string, :default => "", :null => false
    t.column "contact_user_id__c", :string, :default => "", :null => false
    t.column "frequency__c", :string, :default => "", :null => false
    t.column "last_report__c", :datetime, :null => false
    t.column "business_unit__c", :string, :default => "", :null => false
    t.column "notification_last_sent__c", :datetime, :null => false
    t.column "dont_send_empty_report__c", :string, :default => "", :null => false
    t.column "list_alias__c", :string, :default => "", :null => false
    t.column "start_date__c", :date, :null => false
    t.column "orientation_date__c", :date, :null => false
    t.column "laptop__c", :string, :default => "", :null => false
    t.column "linux_workstation__c", :string, :default => "", :null => false
    t.column "sun_workstation__c", :string, :default => "", :null => false
    t.column "special_requests_admin__c", :string, :default => "", :null => false
    t.column "dept__c", :string, :default => "", :null => false
    t.column "special_requests_it__c", :string, :default => "", :null => false
    t.column "employee_number__c", :string, :default => "", :null => false
    t.column "users_without_emp_num__c", :string, :default => "", :null => false
    t.column "contacts_without_emp_num__c", :string, :default => "", :null => false
    t.column "portal_last_login_date__c", :datetime, :null => false
    t.column "portal_login_count__c", :string, :default => "", :null => false
    t.column "portal_last_login_date_fmt__c", :date, :null => false
    t.column "local_name__c", :string, :default => "", :null => false
    t.column "portal_username__c", :string, :default => "", :null => false
    t.column "reassign_to_user_id__c", :string, :default => "", :null => false
    t.column "branches_approved_by_user_id__c", :string, :default => "", :null => false
    t.column "branches_approved_by__c", :string, :default => "", :null => false
    t.column "reassign_to__c", :string, :default => "", :null => false
    t.column "pr_cr_detail_level__c", :string, :default => "", :null => false
    t.column "pr_frequency__c", :string, :default => "", :null => false
    t.column "pr_last_report_date_time__c", :datetime, :null => false
    t.column "pr_no_empty__c", :string, :default => "", :null => false
    t.column "pr_branch_detail_level__c", :string, :default => "", :null => false
    t.column "local_title__c", :string, :default => "", :null => false
    t.column "localized_dept__c", :string, :default => "", :null => false
    t.column "localized_business_unit__c", :string, :default => "", :null => false
    t.column "portal_last_login_fail_date__c", :datetime, :null => false
    t.column "portal_login_fail_count__c", :string, :default => "", :null => false
    t.column "tags__c", :string, :default => "", :null => false
    t.column "portal_login_success__c", :float, :default => 0.0, :null => false
    t.column "portal_total_login_seconds__c", :string, :default => "", :null => false
    t.column "portal_max_login_seconds__c", :string, :default => "", :null => false
    t.column "portal_average_login_seconds__c", :string, :default => "", :null => false
    t.column "order_download_until__c", :date, :null => false
    t.column "order_rtu_id__c", :string, :default => "", :null => false
    t.column "hr_survey__c", :string, :default => "", :null => false
    t.column "license_delivery_contact__c", :string, :default => "", :null => false
    t.column "full_name__c", :string, :default => "", :null => false
    t.column "last_login_failed__c", :string, :default => "", :null => false
    t.column "sf_id", :string, :default => "", :null => false
  end

  create_table "sfsolution", :force => true do |t|
    t.column "solution_number", :string, :default => "", :null => false
    t.column "solution_name", :string, :default => "", :null => false
    t.column "is_published", :string, :default => "", :null => false
    t.column "is_published_in_public_kb", :string, :default => "", :null => false
    t.column "status", :string, :default => "", :null => false
    t.column "record_type_id", :string, :default => "", :null => false
    t.column "is_reviewed", :string, :default => "", :null => false
    t.column "solution_note", :string, :default => "", :null => false
    t.column "owner_id", :string, :default => "", :null => false
    t.column "created_date", :datetime, :null => false
    t.column "created_by_id", :string, :default => "", :null => false
    t.column "last_modified_date", :datetime, :null => false
    t.column "last_modified_by_id", :string, :default => "", :null => false
    t.column "system_modstamp", :datetime, :null => false
    t.column "solution_type__c", :string, :default => "", :null => false
    t.column "account_specific__c", :string, :default => "", :null => false
    t.column "account_name__c", :string, :default => "", :null => false
    t.column "publish_request__c", :string, :default => "", :null => false
    t.column "initial_version__c", :string, :default => "", :null => false
    t.column "final_version__c", :string, :default => "", :null => false
    t.column "special_build__c", :string, :default => "", :null => false
    t.column "effective_date__c", :date, :null => false
    t.column "product_name__c", :string, :default => "", :null => false
    t.column "component__c", :string, :default => "", :null => false
    t.column "sme_reviewer_id__c", :string, :default => "", :null => false
    t.column "sub_status__c", :string, :default => "", :null => false
    t.column "question_problem__c", :string, :default => "", :null => false
    t.column "answer_workaround__c", :string, :default => "", :null => false
    t.column "error_warning_message__c", :string, :default => "", :null => false
    t.column "message_description__c", :string, :default => "", :null => false
    t.column "solution_workaround__c", :string, :default => "", :null => false
    t.column "solution_answer__c", :string, :default => "", :null => false
    t.column "enter_solution_error_message__c", :string, :default => "", :null => false
    t.column "test_solution__c", :string, :default => "", :null => false
    t.column "test_error__c", :string, :default => "", :null => false
    t.column "sf_id", :string, :default => "", :null => false
    t.column "approve__c", :string
    t.column "reject__c", :string
  end

  create_table "sfssl", :force => true do |t|
    t.column "last_name", :string, :default => "", :null => false
    t.column "first_name", :string, :default => "", :null => false
    t.column "username", :string, :default => "", :null => false
    t.column "email", :string, :default => "", :null => false
    t.column "is_active", :string, :default => "", :null => false
    t.column "time_zone_sid_key", :string, :default => "", :null => false
    t.column "locale_sid_key", :string, :default => "", :null => false
    t.column "contact_id", :string, :default => "", :null => false
    t.column "language_locale_key", :string, :default => "", :null => false
    t.column "super_user", :string, :default => "", :null => false
    t.column "last_login_date", :datetime, :null => false
    t.column "created_date", :datetime, :null => false
    t.column "created_by_id", :string, :default => "", :null => false
    t.column "last_modified_date", :datetime, :null => false
    t.column "last_modified_by_id", :string, :default => "", :null => false
    t.column "system_modstamp", :datetime, :null => false
    t.column "sf_id", :string, :default => "", :null => false
  end

  create_table "sfuser", :force => true do |t|
    t.column "username", :string, :default => "", :null => false
    t.column "last_name", :string, :default => "", :null => false
    t.column "first_name", :string, :default => "", :null => false
    t.column "company_name", :string, :default => "", :null => false
    t.column "division", :string, :default => "", :null => false
    t.column "department", :string, :default => "", :null => false
    t.column "title", :string, :default => "", :null => false
    t.column "street", :string, :default => "", :null => false
    t.column "city", :string, :default => "", :null => false
    t.column "state", :string, :default => "", :null => false
    t.column "postal_code", :string, :default => "", :null => false
    t.column "country", :string, :default => "", :null => false
    t.column "email", :string, :default => "", :null => false
    t.column "phone", :string, :default => "", :null => false
    t.column "fax", :string, :default => "", :null => false
    t.column "mobile_phone", :string, :default => "", :null => false
    t.column "alias", :string, :default => "", :null => false
    t.column "is_active", :string, :default => "", :null => false
    t.column "time_zone_sid_key", :string, :default => "", :null => false
    t.column "user_role_id", :string, :default => "", :null => false
    t.column "locale_sid_key", :string, :default => "", :null => false
    t.column "receives_info_emails", :string, :default => "", :null => false
    t.column "receives_admin_info_emails", :string, :default => "", :null => false
    t.column "email_encoding_key", :string, :default => "", :null => false
    t.column "profile_id", :string, :default => "", :null => false
    t.column "language_locale_key", :string, :default => "", :null => false
    t.column "employee_number", :string, :default => "", :null => false
    t.column "last_login_date", :datetime
    t.column "created_date", :datetime
    t.column "created_by_id", :string, :default => "", :null => false
    t.column "last_modified_date", :datetime
    t.column "last_modified_by_id", :string, :default => "", :null => false
    t.column "system_modstamp", :datetime, :null => false
    t.column "offline_trial_expiration_date", :datetime
    t.column "offline_pda_trial_expiration_date", :datetime
    t.column "user_permissions_marketing_user", :string, :default => "", :null => false
    t.column "user_permissions_offline_user", :string, :default => "", :null => false
    t.column "user_permissions_avantgo_user", :string, :default => "", :null => false
    t.column "forecast_enabled", :string, :default => "", :null => false
    t.column "reports_to__c", :string, :default => "", :null => false
    t.column "lookup_user__c", :string, :default => "", :null => false
    t.column "ex_employee__c", :string, :default => "", :null => false
    t.column "user_contact_id__c", :string, :default => "", :null => false
    t.column "description__c", :string, :default => "", :null => false
    t.column "sf_id", :string, :default => "", :null => false
  end

end
