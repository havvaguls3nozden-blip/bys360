-- BYS360 Eğitim Yönetimi Faz 6 yardımcı SQL'i
-- Amaç: sertifika ve audit tablolarını güvenli şekilde oluşturmak
-- Not: mümkünse önce Alembic migration üretilerek uygulanmalıdır.

BEGIN;

CREATE TABLE IF NOT EXISTS education_audit_logs (
    id SERIAL PRIMARY KEY,
    education_record_id INTEGER NULL REFERENCES education_records(id) ON DELETE CASCADE,
    education_participant_id INTEGER NULL REFERENCES education_participants(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL,
    summary VARCHAR(255) NULL,
    details_json TEXT NULL,
    actor_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_education_audit_logs_education_record_id ON education_audit_logs (education_record_id);
CREATE INDEX IF NOT EXISTS ix_education_audit_logs_education_participant_id ON education_audit_logs (education_participant_id);
CREATE INDEX IF NOT EXISTS ix_education_audit_logs_action ON education_audit_logs (action);

CREATE TABLE IF NOT EXISTS education_certificate_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    organization_name VARCHAR(255) NULL,
    certificate_title VARCHAR(255) NOT NULL DEFAULT 'Katılım Sertifikası',
    subtitle VARCHAR(255) NULL,
    body_template TEXT NOT NULL DEFAULT 'Bu sertifika, {participant_name} isimli personelin {education_title} eğitimine katıldığını belgelemek amacıyla düzenlenmiştir.',
    footer_text TEXT NULL,
    serial_prefix VARCHAR(30) NOT NULL DEFAULT 'EGT',
    accent_color VARCHAR(20) NOT NULL DEFAULT '#8B0000',
    verification_base_url VARCHAR(500) NULL,
    page_orientation VARCHAR(20) NOT NULL DEFAULT 'landscape',
    city_name VARCHAR(100) NULL,
    issue_date_label VARCHAR(100) NOT NULL DEFAULT 'Düzenlenme Tarihi',
    background_image_path VARCHAR(500) NULL,
    logo_path VARCHAR(500) NULL,
    signer_1_name VARCHAR(255) NULL,
    signer_1_title VARCHAR(255) NULL,
    signer_1_image_path VARCHAR(500) NULL,
    signer_2_name VARCHAR(255) NULL,
    signer_2_title VARCHAR(255) NULL,
    signer_2_image_path VARCHAR(500) NULL,
    show_qr BOOLEAN NOT NULL DEFAULT TRUE,
    created_by_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    updated_by_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_education_certificate_templates_is_active ON education_certificate_templates (is_active);

CREATE TABLE IF NOT EXISTS education_certificates (
    id SERIAL PRIMARY KEY,
    education_record_id INTEGER NOT NULL REFERENCES education_records(id) ON DELETE CASCADE,
    participant_id INTEGER NOT NULL REFERENCES education_participants(id) ON DELETE CASCADE,
    template_id INTEGER NOT NULL REFERENCES education_certificate_templates(id) ON DELETE RESTRICT,
    certificate_no VARCHAR(100) NOT NULL UNIQUE,
    verification_code VARCHAR(64) NOT NULL UNIQUE,
    status VARCHAR(30) NOT NULL DEFAULT 'active',
    issued_by_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    issued_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    pdf_relative_path VARCHAR(500) NULL,
    render_version INTEGER NOT NULL DEFAULT 1,
    revoked_at TIMESTAMP WITHOUT TIME ZONE NULL,
    revoke_reason TEXT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_education_certificates_education_record_id ON education_certificates (education_record_id);
CREATE INDEX IF NOT EXISTS ix_education_certificates_participant_id ON education_certificates (participant_id);
CREATE INDEX IF NOT EXISTS ix_education_certificates_template_id ON education_certificates (template_id);
CREATE INDEX IF NOT EXISTS ix_education_certificates_status ON education_certificates (status);

CREATE TABLE IF NOT EXISTS education_certificate_logs (
    id SERIAL PRIMARY KEY,
    certificate_id INTEGER NOT NULL REFERENCES education_certificates(id) ON DELETE CASCADE,
    actor_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,
    note TEXT NULL,
    ip_address VARCHAR(64) NULL,
    user_agent VARCHAR(500) NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_education_certificate_logs_certificate_id ON education_certificate_logs (certificate_id);

INSERT INTO education_certificate_templates (
    name, is_active, organization_name, certificate_title, subtitle, body_template,
    serial_prefix, accent_color, page_orientation, issue_date_label, show_qr
)
SELECT
    'Varsayılan Kurumsal Şablon', TRUE, 'Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı',
    'Katılım Sertifikası', 'Eğitim Yönetimi Modülü Varsayılan Şablonu',
    'Bu sertifika, {participant_name} isimli personelin {education_title} eğitimine katıldığını belgelemek amacıyla düzenlenmiştir.',
    'EGT', '#8B0000', 'landscape', 'Düzenlenme Tarihi', TRUE
WHERE NOT EXISTS (
    SELECT 1 FROM education_certificate_templates
);

COMMIT;
