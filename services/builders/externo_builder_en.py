# sigp/services/builders/juridica_builder_en.py

from datetime import datetime
from sigp.services.builders.utils import (
    draw_header, draw_centered, draw_right, 
    draw_paragraph, draw_bullets
)

def english_long_date():
    """Genera la fecha en formato largo en inglés"""
    return datetime.utcnow().strftime("%B %d, %Y")

def build(c, prescriptor, datos):
    width, height = datos["width"], datos["height"]
    margin_x = 72
    
    # Extraemos datos
    nombre_entidad = getattr(prescriptor, "company_name", datos["name"]) 
    nombre_representante = datos["name"]
    doc_type, doc_num, domicile = datos["doc_type"], datos["doc_num"], datos["domicile"]
    
    # DIBUJO DEL ENCABEZADO Y TÍTULOS
    draw_header(c, width, height)
    y = height - 120
    
    draw_centered(c, "COMMERCIAL COLLABORATION AGREEMENT - PRESCRIBERS PROGRAM externo", width, y, size=13)
    y -= 20
    draw_centered(c, "between", width, y, font="Helvetica", size=11)
    y -= 20
    draw_centered(c, "INNOVA TRAINING CONSULTORIA Y FORMACION S.L. SPORTS DATA CAMPUS", width, y, size=12)
    y -= 20
    draw_centered(c, "and", width, y, font="Helvetica", size=11)
    y -= 20
    draw_centered(c, nombre_entidad.upper(), width, y, size=12)

    y -= 40
    fecha_larga = english_long_date()
    draw_right(c, f"In {datos['ciudad']}, on {fecha_larga}.", width, y)

    y -= 40
    draw_centered(c, "BY AND BETWEEN", width, y, size=12)
    y -= 30

    y = draw_paragraph(c, "On the one hand,", margin_x, y, width - 2*margin_x, height, font="Helvetica-Oblique")
    y = draw_paragraph(c, "Mr. Jesús Serrano Sanz, with ID No. 09.303.401-Q, acting in his capacity as Sole Administrator and on behalf of INNOVA TRAINING CONSULTORIA Y FORMACION S.L., owner of the trademark “Sports Data Campus”, with VAT No. B19456128 and registered office at C/ del Campo de Gomara, 4, CP 47008, Valladolid, Spain (hereinafter, THE COMPANY).", margin_x, y, width - 2*margin_x, height)
    
    y -= 10
    y = draw_paragraph(c, "And on the other hand,", margin_x, y, width - 2*margin_x, height, font="Helvetica-Oblique")
    y = draw_paragraph(c, f"Mr./Ms. {nombre_representante.upper()}, with {doc_type} No. {doc_num}, acting on behalf of {nombre_entidad.upper()}, with registered office at {domicile}, with sufficient powers to bind said entity in this agreement (hereinafter, THE COLLABORATOR).", margin_x, y, width - 2*margin_x, height)

    y -= 10
    y = draw_paragraph(c, "Both parties, mutually acknowledging the necessary legal capacity to enter into this agreement,", margin_x, y, width - 2*margin_x, height)

    y -= 20
    draw_centered(c, "RECITALS", width, y, size=12)
    y -= 30
    
    y = draw_paragraph(c, "That they are interested in establishing a collaboration framework within the Sports Data Campus Prescribers Program, with the objective of promoting and recommending the training programs taught by THE COMPANY.", margin_x, y, width - 2*margin_x, height)
    y = draw_paragraph(c, "By virtue of the foregoing, they agree to formalize this Commercial Collaboration Agreement, which shall be governed by the following:", margin_x, y, width - 2*margin_x, height)

    y -= 20
    draw_centered(c, "CLAUSES", width, y, size=12)
    y -= 30

    # CLÁUSULA 1
    y = draw_paragraph(c, "FIRST.– OBJECT OF THE AGREEMENT", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    y = draw_paragraph(c, "This agreement aims to regulate the participation of THE COLLABORATOR in the Sports Data Campus Prescribers Program, through which they may recommend and promote the training programs taught by THE COMPANY, with the objective of facilitating the acquisition of potential students interested in said programs.", margin_x, y, width - 2*margin_x, height)
    y = draw_paragraph(c, "Within the framework of this agreement, THE COLLABORATOR may identify and refer interested prospects (hereinafter, leads) which will be managed and registered through the SIGP (Comprehensive Prescriber Management System) or the official platforms determined by THE COMPANY.", margin_x, y, width - 2*margin_x, height)
    y = draw_paragraph(c, "This agreement exclusively regulates the participation of THE COLLABORATOR in the Sports Data Campus Prescribers Program and is independent of any other professional, commercial, or institutional relationship that may exist between the parties.", margin_x, y, width - 2*margin_x, height)
    y = draw_paragraph(c, "The activity developed by THE COLLABORATOR will be carried out with full organizational autonomy and under their own responsibility, without there being in any case an employment, corporate, or dependency relationship between the parties.", margin_x, y, width - 2*margin_x, height)
    y = draw_paragraph(c, "In no case shall THE COLLABORATOR be empowered to act in the name or on behalf of THE COMPANY, nor to assume commitments, formalize agreements, or modify commercial conditions on behalf of Sports Data Campus before third parties.", margin_x, y, width - 2*margin_x, height)
    y -= 10

    # CLÁUSULA 2
    y = draw_paragraph(c, "SECOND.– COMMISSION SYSTEM FOR CONVERTED ENROLLMENTS", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    y = draw_paragraph(c, "2.1 Commission for Converted Enrollment", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "THE COLLABORATOR shall have the right to receive an economic commission for each converted enrollment originating from a valid lead previously registered in the SIGP and assigned in accordance with the rules established in this agreement.", margin_x, y, width - 2*margin_x, height)
    y = draw_paragraph(c, "For the purposes of this agreement, a converted enrollment shall be understood as one in which the student referred by THE COLLABORATOR has formalized their registration in a training program taught by THE COMPANY and has made the effective payment that triggers the accrual of the corresponding commission.", margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "2.2 Commission Amounts", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "The applicable commissions shall be as follows:", margin_x, y, width - 2*margin_x, height)
    
    comisiones_list = [
        "Master's programs taught in English: 300€ per converted enrollment.",
        "Master's programs taught in Spanish or Portuguese: 150€ per converted enrollment.",
        "Diplomas and short courses: 50€."
    ]
    y = draw_bullets(c, comisiones_list, margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "THE COMPANY may update this commission system when there are changes in its commercial policy or in its training programs structure, committing to communicate such modifications with a minimum notice of thirty (30) calendar days.", margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "2.3 Economic Conditions", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "The commissions established in this agreement shall be understood as gross amounts, including indirect taxes and fees, being subject, in each case, to the applicable tax regulations according to the legal nature, tax situation, and origin of THE COLLABORATOR.", margin_x, y, width - 2*margin_x, height)
    y = draw_paragraph(c, "In the event that THE COLLABORATOR is a legal entity or professional obliged to issue an invoice, the commissions will be paid upon presentation of the corresponding invoice in accordance with current legislation.", margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "2.4 Registration and Determination of Commissions", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "All converted enrollments, as well as the corresponding commissions, will be registered in the SIGP, which will constitute the only valid source for determining:", margin_x, y, width - 2*margin_x, height)
    y = draw_bullets(c, ["Lead assignment", "Conversion to enrollment", "Applicable commission amount", "Accrual and settlement status."], margin_x, y, width - 2*margin_x, height)
    y -= 10

    # CLÁUSULA 3
    y = draw_paragraph(c, "THIRD.– ACCRUAL AND SETTLEMENT OF COMMISSIONS", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    y = draw_paragraph(c, "3.1 Accrual of the Commission", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "The commission corresponding to a converted enrollment shall accrue at the moment the student referred by THE COLLABORATOR has made the effective payment of the enrollment fee for the corresponding training program, and said payment has been received and validated by THE COMPANY in accordance with its internal collection systems.", margin_x, y, width - 2*margin_x, height)
    y = draw_paragraph(c, "For the purposes of this agreement, effective enrollment payment shall be understood as that initial payment or enrollment confirmation that allows formalizing the incorporation of the student into the corresponding training program according to THE COMPANY's administrative procedures.", margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "3.2 Validation of Commissions", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "Accrued commissions will be verified by THE COMPANY's Administration department, which will confirm the validity of the enrollment, the lead assignment, and the absence of financial incidents associated with the payment made by the student.", margin_x, y, width - 2*margin_x, height)
    y = draw_paragraph(c, "Once the corresponding information is validated, the commission will be approved for settlement.", margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "3.3 Settlement and Payment", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "Approved commissions will be settled on a monthly basis.", margin_x, y, width - 2*margin_x, height)
    y = draw_paragraph(c, "Payment will be made within the first ten (10) business days of the month following the accrual of the commission, provided that the corresponding invoice has been received from THE COLLABORATOR if required under applicable tax regulations.", margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "3.4 Conditions for Payment", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "The payment of commissions shall be subject to the following conditions:", margin_x, y, width - 2*margin_x, height)
    y = draw_bullets(c, [
        "That the enrollment has been validated according to THE COMPANY's systems;",
        "That the student's payment has not been subject to a refund, bank chargeback, or financial incident;",
        "That the lead assignment is correctly registered in the SIGP."
    ], margin_x, y, width - 2*margin_x, height)
    y -= 10

    # CLÁUSULA 4
    y = draw_paragraph(c, "FOURTH.– MANAGEMENT OF CANCELLATIONS AND ADJUSTMENTS", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    y = draw_paragraph(c, "4.1 Grounds for Regularization", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "Commissions accrued in accordance with the Second Clause may be subject to regularization in the following cases:", margin_x, y, width - 2*margin_x, height)
    y = draw_bullets(c, [
        "a) When the training program is not ultimately taught due to organizational reasons or failure to reach the minimum number of students.",
        "b) When the student exercises their right of withdrawal or requests cancellation within the legal or contractual periods established by THE COMPANY.",
        "c) When a total or partial refund of the amount paid by the student occurs for any duly justified cause.",
        "d) When there is non-payment, bank chargeback, or any financial incident that implies the total or partial cancellation of the payment that gave rise to the commission accrual."
    ], margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "4.2 Effects of Regularization", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "In the cases described in the previous section:", margin_x, y, width - 2*margin_x, height)
    y = draw_bullets(c, [
        "If the commission has not yet been paid, it will not be settled.",
        "If the commission has already been paid, the corresponding amount may be offset in the next monthly settlement through the current account system between the parties.",
        "In the event that there are no future invoices, the amount must be returned by the prescriber through the same payment method by which it was received."
    ], margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "4.3 Current Account System", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "For the purposes of economic management between the parties, a current account system is established, which will reflect:", margin_x, y, width - 2*margin_x, height)
    y = draw_bullets(c, ["Debits: commissions accrued in favor of THE COLLABORATOR.", "Credits: adjustments derived from cancellations, refunds, or financial incidents."], margin_x, y, width - 2*margin_x, height)
    y = draw_paragraph(c, "In the event that the prescriber has no credit balance, they must return the appropriate amounts derived from the aforementioned cases through the same payment method by which the commissions were received. Balance compensation may be performed automatically in subsequent settlements until full regularization of the corresponding amount.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "4.4 Registration and Transparency", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "All incidents, cancellations, refunds, or adjustments related to converted enrollments will be registered in the SIGP, which will constitute the only valid source for determining the status of each enrollment and the associated commissions.", margin_x, y, width - 2*margin_x, height)
    y -= 10

    # CLÁUSULA 5
    y = draw_paragraph(c, "FIFTH.– QUALITY CONTROL AND LEAD MANAGEMENT", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    y = draw_paragraph(c, "5.1 Definition of a Valid Lead", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "For the purposes of this agreement, a valid lead shall be considered that prospect which simultaneously meets the following conditions:", margin_x, y, width - 2*margin_x, height)
    y = draw_bullets(c, [
        "a) Provides complete, truthful, and verifiable contact information.",
        "b) Expresses a genuine interest in THE COMPANY's training programs.",
        "c) Meets the minimum access requirements for the corresponding training program.",
        "d) Does not constitute duplicate, fraudulent information, or information previously registered in the SIGP by another prescriber within the current assignment period."
    ], margin_x, y, width - 2*margin_x, height)
    y = draw_paragraph(c, "THE COMPANY reserves the right to validate the condition of a valid lead according to the internal criteria established in the SIGP.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "5.2 Registration and Assignment of Leads", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "For a lead to generate a right to commission, it must be previously registered in the SIGP or on the official platforms determined by THE COMPANY. The assignment of the lead will correspond to the prescriber who correctly registered it in the SIGP first.", margin_x, y, width - 2*margin_x, height)
    y = draw_paragraph(c, "Such assignment will remain valid for a period of six (6) months from the date of registration. Once this period has elapsed without a converted enrollment, the lead may be worked by other prescribers, with the former losing exclusivity over it.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "5.3 Traceability and Determination of Ownership", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "The seniority, ownership, and status of the leads will be determined exclusively by the registration made in the SIGP, which has an auditing system and internal activity log. The SIGP will constitute the only valid and binding source for determining: Lead ownership, Registration date, Conversion to enrollment, Commission accrual and status.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "5.4 Territoriality and Exclusivity", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "Given that THE COMPANY's training activity is primarily developed online, this agreement does not establish territorial exclusivity. THE COLLABORATOR may promote the training programs in any geographical area. The commission will belong exclusively to the prescriber who validly registered the lead in the SIGP within the established assignment period.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "5.5 Resolution of Disputes", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "In the event of a dispute over the ownership of a lead or the assignment of a converted enrollment, THE COMPANY will resolve the incident taking as a reference the information registered in the SIGP and the internal validation criteria of the Prescribers Program.", margin_x, y, width - 2*margin_x, height)
    y -= 10

    # CLÁUSULA 6
    y = draw_paragraph(c, "SIXTH.– DATABASE OWNERSHIP AND USE OF INFORMATION", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    y = draw_paragraph(c, "6.1 Data Ownership", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "All leads, contact details, commercial information, and any other data generated, captured, or managed under this agreement shall be the exclusive property of THE COMPANY. Such information will be managed through the SIGP or the official platforms determined by THE COMPANY.", margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "6.2 Limitation of Use", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "THE COLLABORATOR acquires no rights of ownership, title, or exploitation over the data generated within the framework of this agreement. THE COLLABORATOR undertakes to use such information exclusively for the purposes established in this agreement and in accordance with THE COMPANY's instructions and guidelines, respecting at all times the current Data Protection legislation of each territory.", margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "6.3 Prohibition of External Use", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "It is expressly prohibited for THE COLLABORATOR to:", margin_x, y, width - 2*margin_x, height)
    y = draw_bullets(c, [
        "Use the data obtained under this agreement for purposes other than the promotion of THE COMPANY's training programs;",
        "Incorporate the data into their own or third-party databases;",
        "Market products or services unrelated to THE COMPANY using the information obtained during the term of this agreement."
    ], margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "6.4 Termination of the Agreement", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "Upon termination of this agreement, for whatever cause, THE COLLABORATOR must:", margin_x, y, width - 2*margin_x, height)
    y = draw_bullets(c, [
        "Immediately cease using the data and any information obtained through the Prescribers Program;",
        "Delete or destroy any copy or record of data in their possession;",
        "Refrain from contacting the leads generated under this agreement again, except with express written authorization from THE COMPANY."
    ], margin_x, y, width - 2*margin_x, height)
    y -= 10

    # CLÁUSULA 7
    y = draw_paragraph(c, "SEVENTH.– OBLIGATIONS OF THE PARTIES", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    y = draw_paragraph(c, "7.1 Obligations of THE COMPANY", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_bullets(c, [
        "Provide THE COLLABORATOR with the commercial information, promotional materials, and documentation necessary for the proper promotion of the training programs.",
        "Provide access to the SIGP or other official tools necessary for the registration and tracking of leads.",
        "Correctly register and process converted enrollments and accrued commissions in accordance with the provisions of this agreement.",
        "Proceed with the payment of the corresponding commissions within the terms and conditions established in the agreement.",
        "Keep the current commission system updated and communicate in writing any modification with a minimum notice of thirty (30) calendar days, unless such modification derives from legal or regulatory obligations of immediate application."
    ], margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "7.2 Obligations of THE COLLABORATOR", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_bullets(c, [
        "Promote THE COMPANY's training programs professionally, ethically, and in accordance with the image, values, and commercial guidelines established by Sports Data Campus.",
        "Register all leads exclusively through the SIGP or the official channels established by THE COMPANY.",
        "Comply with current regulations regarding data protection, commercial communications, and any other regulation applicable to their activity.",
        "Not offer economic conditions, discounts, scholarships, guarantees, or promises that are not expressly authorized by THE COMPANY.",
        "Inform THE COMPANY of any relevant incident related to the managed leads or students.",
        "Act at all times as an independent collaborator, without holding legal representation or the capacity to contractually bind THE COMPANY before third parties."
    ], margin_x, y, width - 2*margin_x, height)
    y -= 10

    # CLÁUSULA 8
    y = draw_paragraph(c, "EIGHTH.– DURATION AND TERMINATION OF THE AGREEMENT", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    y = draw_paragraph(c, "8.1 Duration", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "This agreement will have an initial duration of one (1) year from the date of its signature. At the end of said period, the agreement will be automatically renewed for successive periods of one (1) year, unless either party notifies in writing its intention not to renew with a minimum notice of thirty (30) calendar days prior to the expiration date.", margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "8.2 Early Termination", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "This agreement may be terminated early in the following cases:", margin_x, y, width - 2*margin_x, height)
    y = draw_bullets(c, [
        "a) Due to a serious breach of any of the obligations established in this agreement.",
        "b) By mutual agreement between the parties, formalized in writing.",
        "c) By unilateral decision of either party, with a written notice of at least thirty (30) calendar days."
    ], margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "8.3 Prescriber Inactivity", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "For the purposes of this agreement, THE COLLABORATOR shall be considered inactive when they have not registered any valid lead in the SIGP for a continuous period of three (3) months. In such cases, THE COMPANY may consider THE COLLABORATOR's participation in the Prescribers Program finalized or invite them to adhere to the current conditions of the program at that time.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "8.4 Effects of Termination", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "In case of termination of this agreement:", margin_x, y, width - 2*margin_x, height)
    y = draw_bullets(c, [
        "THE COLLABORATOR will no longer have the right to register new leads from the effective date of termination.",
        "Only commissions accrued in accordance with the provisions of this agreement and not subject to regularization according to previous clauses will be settled.",
        "Obligations regarding confidentiality, data protection, and use of information will remain in effect after the termination of the agreement."
    ], margin_x, y, width - 2*margin_x, height)
    y -= 10

    # CLÁUSULA 9
    y = draw_paragraph(c, "NINTH.– CONFIDENTIALITY", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    y = draw_paragraph(c, "9.1 Confidential Information", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "THE COLLABORATOR undertakes to maintain the strictest confidentiality regarding all information they access as a result of the execution of this agreement.", margin_x, y, width - 2*margin_x, height)
    y = draw_paragraph(c, "For the purposes of this agreement, confidential information shall be considered any technical, commercial, strategic, financial, or other nature of information belonging to THE COMPANY, including, among others: Commercial or strategic information of Sports Data Campus; Economic, financial, or billing data; Commercial or contractual conditions applicable to the training programs; Information regarding students, leads, or clients; Internal functioning of the SIGP or other technological tools used by THE COMPANY. The information will be considered confidential even when it is not expressly identified as such, provided that by its nature it should reasonably be treated as reserved information.", margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "9.2 Scope of the Obligation", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_bullets(c, [
        "Not to disclose confidential information to third parties without prior written authorization from THE COMPANY;",
        "Not to use the confidential information for purposes other than those derived from the execution of this agreement;",
        "To adopt the necessary measures to prevent unauthorized access to such information."
    ], margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "9.3 Validity of Confidentiality", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "The confidentiality obligation will remain in force during the term of this agreement and will continue in effect for a minimum period of five (5) years after its termination, for whatever cause.", margin_x, y, width - 2*margin_x, height)
    y -= 10

    # CLÁUSULA 10
    y = draw_paragraph(c, "TENTH.– DATA PROTECTION", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    y = draw_paragraph(c, "10.1 Regulatory Framework", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "The parties undertake to comply with the provisions of Regulation (EU) 2016/679 of the European Parliament and of the Council, of April 27, 2016 (GDPR), as well as with Organic Law 3/2018 on the Protection of Personal Data and guarantee of digital rights (LOPDGDD) and other current regulations regarding the protection of personal data.", margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "10.2 Data Processing", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "THE COLLABORATOR will process the personal data they access exclusively for the correct execution of this agreement and in accordance with THE COMPANY's instructions. In particular, THE COLLABORATOR undertakes to:", margin_x, y, width - 2*margin_x, height)
    y = draw_bullets(c, [
        "a) Not use personal data for their own purposes or purposes other than those provided for in this agreement.",
        "b) Not transfer personal data to third parties without prior and express authorization from THE COMPANY, except due to legal obligation.",
        "c) Apply the appropriate technical and organizational measures to ensure the security and confidentiality of the processed personal data."
    ], margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "10.3 Security and Incidents", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "THE COLLABORATOR undertakes to inform THE COMPANY immediately in the event of detecting any security incident, unauthorized access, loss, or breach affecting personal data linked to this agreement.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "10.4 Termination of Processing", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "Upon termination of this agreement, THE COLLABORATOR must: Delete or return to THE COMPANY all personal data accessed within the framework of this agreement; Refrain from keeping copies of such data, unless there is a legal obligation to retain them.", margin_x, y, width - 2*margin_x, height)
    y -= 10

    # CLÁUSULA 11
    y = draw_paragraph(c, "ELEVENTH.– SUBSTITUTION OF PREVIOUS AGREEMENTS AND TRANSITION", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    y = draw_paragraph(c, "11.1 Substitution of Previous Agreements", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "This agreement replaces and renders null and void any previous agreement, convention, or understanding existing between the parties regarding participation in prescriber programs or commercial collaboration linked to THE COMPANY's training programs, whether of a verbal or written nature. In case of contradiction between this agreement and any previous document signed between the parties regarding the same object, the provisions of this agreement shall prevail.", margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "11.2 Prescribers with Previous Activity", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "Notwithstanding the foregoing, in those cases where THE COLLABORATOR had generated effective commercial activity prior to the signing of this agreement, THE COMPANY may temporarily maintain the previously agreed conditions until their express review or renegotiation between the parties.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "11.3 Inactive Prescribers", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "For the purposes of this agreement, a prescriber will be considered in a state of inactivity when they have not registered any valid lead in the SIGP for a continuous period of three (3) months. In such cases, THE COMPANY may consider the previous agreement extinguished and offer the prescriber adherence to the current model of the Prescribers Program.", margin_x, y, width - 2*margin_x, height)
    y -= 10

    # CLÁUSULA 12
    y = draw_paragraph(c, "TWELFTH.– APPLICABLE LAW AND JURISDICTION", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    y = draw_paragraph(c, "This agreement has a commercial nature and shall be governed and interpreted in accordance with current Spanish legislation. For the resolution of any controversy, discrepancy, or conflict that may arise from the interpretation, execution, or validity of this agreement, the parties expressly submit to the jurisdiction of the Courts and Tribunals of Valladolid, Spain, expressly waiving any other jurisdiction that may correspond to them.", margin_x, y, width - 2*margin_x, height)

    # FINAL: CAJAS DE FIRMA
    if y < 220:
        c.showPage()
        y = height - 72
        draw_header(c, width, height)
        
    y_sig_base = y - 100
    c.setFont("Helvetica", 10)
    
    # Firma Presidente
    c.drawString(80, y_sig_base + 65, "For Innova Training:")
    c.drawString(80, y_sig_base + 53, "Jesús Serrano Sanz")
    c.drawString(80, y_sig_base + 41, "President and Sole Administrator")
    c.rect(80, y_sig_base - 20, 220, 55)
    
    # Firma Prescriptor
    c.drawString(320, y_sig_base + 65, "For THE COLLABORATOR:")
    c.drawString(320, y_sig_base + 53, nombre_representante)
    c.rect(320, y_sig_base - 20, 220, 55)