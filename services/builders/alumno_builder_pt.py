# sigp/services/builders/alumno_builder_pt.py

from datetime import datetime

from sigp.services.builders.utils import (
    draw_header,
    draw_centered,
    draw_right,
    draw_paragraph,
    draw_bullets,
    draw_signatures,
)


def portuguese_long_date() -> str:
    dt = datetime.utcnow()
    meses = [
        "janeiro",
        "fevereiro",
        "março",
        "abril",
        "maio",
        "junho",
        "julho",
        "agosto",
        "setembro",
        "outubro",
        "novembro",
        "dezembro",
    ]
    return f"aos {dt.day} dias do mês de {meses[dt.month - 1]} de {dt.year}"


def _paragraphs(c, paragraphs, margin_x, y, width, height, *, font="Helvetica", size=11):
    for paragraph in paragraphs:
        y = draw_paragraph(c, paragraph, margin_x, y, width - 2 * margin_x, height, font=font, size=size)
    return y


def build(c, prescriptor, datos):
    width, height = datos["width"], datos["height"]
    margin_x = 72

    nome_entidade = getattr(prescriptor, "company_name", datos["name"])
    nome_representante = datos["name"]
    doc_type, doc_num, domicile = datos["doc_type"], datos["doc_num"], datos["domicile"]

    draw_header(c, width, height)
    y = height - 120

    draw_centered(c, "ACORDO DE COLABORAÇÃO COMERCIAL - PROGRAMA DE PRESCRITORES", width, y, size=13)
    y -= 20
    draw_centered(c, "entre", width, y, font="Helvetica", size=11)
    y -= 20
    draw_centered(c, "INNOVA TRAINING CONSULTORIA Y FORMACION S.L.\nSPORTS DATA CAMPUS", width, y, size=12)
    y -= 20
    draw_centered(c, "e", width, y, font="Helvetica", size=11)
    y -= 20
    draw_centered(c, nome_entidade.upper(), width, y, size=12)

    y -= 40
    draw_right(c, f"Em Valladolid, {portuguese_long_date()}.", width, y)

    y -= 40
    draw_centered(c, "REUNIDOS", width, y, size=12)
    y -= 30

    y = draw_paragraph(c, "De uma parte,", margin_x, y, width - 2 * margin_x, height, font="Helvetica-Oblique")
    y = draw_paragraph(
        c,
        "Don Jesús Serrano Sanz, com D.N.I. nº 09.303.401-Q, atuando na qualidade de Administrador Único e em nome e representação da INNOVA TRAINING CONSULTORIA Y FORMACION S.L., proprietária da marca comercial Sports Data Campus, com C.I.F. nº B19456128 e domicílio social em C/ del Campo de Gomara, 4, CP 47008, Valladolid, Espanha (doravante, A EMPRESA).",
        margin_x,
        y,
        width - 2 * margin_x,
        height,
    )
    y -= 10
    y = draw_paragraph(c, "E de outra parte,", margin_x, y, width - 2 * margin_x, height, font="Helvetica-Oblique")
    y = draw_paragraph(
        c,
        f"Sr./Sra. {nome_representante.upper()}, com {doc_type} nº {doc_num}, com domicílio em {domicile}, que atua em seu próprio nome e direito, e que participa ou participou como aluno em um dos programas formativos ministrados pela Sports Data Campus (doravante, O COLABORADOR).",
        margin_x,
        y,
        width - 2 * margin_x,
        height,
    )

    y -= 10
    y = draw_paragraph(
        c,
        "Ambas as partes, reconhecendo mutuamente a capacidade legal necessária para se obrigarem pelo presente acordo,",
        margin_x,
        y,
        width - 2 * margin_x,
        height,
    )

    y -= 20
    draw_centered(c, "EXPÕEM", width, y, size=12)
    y -= 30

    y = _paragraphs(
        c,
        [
            "Que o programa tem por objetivo fomentar a participação da comunidade acadêmica da Sports Data Campus na divulgação dos seus programas formativos, reconhecendo essa colaboração por meio de um sistema de bonificações formativas ou benefícios equivalentes.",
            "Em virtude do exposto, as partes acordam formalizar o presente Acordo de Colaboração dentro do Programa de Prescritores, que se regerá pelas seguintes:",
        ],
        margin_x,
        y,
        width,
        height,
    )

    y -= 20
    draw_centered(c, "CLÁUSULAS", width, y, size=12)
    y -= 30

    y = draw_paragraph(c, "PRIMEIRA.- OBJETO DO ACORDO", margin_x, y, width - 2 * margin_x, height, font="Helvetica-Bold")
    y = _paragraphs(
        c,
        [
            "O presente acordo tem por objeto regular a participação de O COLABORADOR no Programa de Prescritores da Sports Data Campus. Nessa condição de aluno, poderá recomendar e divulgar os programas formativos ministrados por A EMPRESA a potenciais interessados, contribuindo para o crescimento e fortalecimento da comunidade acadêmica da Sports Data Campus.",
            "No âmbito deste acordo, O COLABORADOR poderá identificar e encaminhar potenciais interessados (doravante, leads), que serão geridos e registrados através do SIGP (Sistema Integral de Gestão de Prescritores) ou das plataformas oficiais que A EMPRESA determine.",
            "O presente acordo regula exclusivamente a participação de O COLABORADOR no Programa de Prescritores da Sports Data Campus e é independente de qualquer outra relação acadêmica, profissional ou institucional que possa existir entre as partes.",
            "A atividade desenvolvida por O COLABORADOR será realizada de forma voluntária e com plena autonomia, sem que exista, em qualquer caso, relação laboral, comercial de agência ou dependência entre as partes.",
            "Em nenhum caso O COLABORADOR estará autorizado a atuar em nome ou representação de A EMPRESA, assumir compromissos, formalizar acordos ou modificar condições comerciais em nome da Sports Data Campus perante terceiros.",
            "A participação de O COLABORADOR limita-se exclusivamente à identificação, recomendação e encaminhamento qualificado de potenciais interessados nos programas formativos de A EMPRESA.",
            "O COLABORADOR não realizará atividades de venda, negociação, fechamento comercial ou formalização de matrículas, funções que correspondem exclusivamente ao Departamento Comercial de A EMPRESA.",
            "O COLABORADOR também não estará autorizado a estabelecer condições econômicas, oferecer descontos, comprometer vagas ou realizar promessas comerciais em nome de A EMPRESA perante terceiros.",
        ],
        margin_x,
        y,
        width,
        height,
    )

    y -= 10
    y = draw_paragraph(c, "SEGUNDA.- SISTEMA DE BONIFICAÇÕES POR MATRÍCULA CONVERTIDA", margin_x, y, width - 2 * margin_x, height, font="Helvetica-Bold")
    y = draw_paragraph(c, "\n2.1 Bonificação por Matrícula Convertida", margin_x, y, width - 2 * margin_x, height, font="Helvetica-Bold", size=10)
    y = _paragraphs(
        c,
        [
            "O COLABORADOR terá direito a receber uma bonificação dentro do Programa de Prescritores por cada matrícula convertida proveniente de um lead válido previamente registrado no SIGP e atribuído conforme as regras estabelecidas no presente acordo.",
            "Para os efeitos deste acordo, considera-se matrícula convertida aquela em que o aluno indicado por O COLABORADOR tenha formalizado sua inscrição em um programa formativo ministrado por A EMPRESA e tenha realizado o pagamento efetivo que ativa o reconhecimento da bonificação correspondente.",
            "As bonificações geradas poderão materializar-se mediante benefícios formativos, créditos acadêmicos ou redução de custos em programas ministrados pela Sports Data Campus, conforme as condições estabelecidas nas cláusulas seguintes.",
        ],
        margin_x,
        y,
        width,
        height,
    )
    y = draw_paragraph(c, "\n2.2 Valor das bonificações", margin_x, y, width - 2 * margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "As bonificações geradas por matrículas de recomendados de O COLABORADOR convertidas serão atribuídas conforme o seguinte valor equivalente dentro do sistema de benefícios formativos da Sports Data Campus:", margin_x, y, width - 2 * margin_x, height)
    y = draw_bullets(
        c,
        [
            "Mestrados ministrados em inglês: 300€ por matrícula convertida.",
            "Mestrados ministrados em espanhol ou português: 150€ por matrícula convertida.",
            "Diplomados e cursos de duração mais curta: 50€ por matrícula convertida.",
        ],
        margin_x,
        y,
        width - 2 * margin_x,
        height,
    )
    y = _paragraphs(
        c,
        [
            "Esses valores serão acumulados na conta do colaborador dentro do Programa de Prescritores e poderão ser aplicados como créditos formativos, redução de matrícula ou outros benefícios acadêmicos oferecidos por A EMPRESA.",
            "A EMPRESA poderá atualizar o sistema de bonificações quando houver alterações em sua política acadêmica ou na estrutura dos programas formativos, comprometendo-se a comunicar tais modificações com antecedência mínima de trinta (30) dias corridos.",
        ],
        margin_x,
        y,
        width,
        height,
    )
    y = draw_paragraph(c, "\n2.3 Aplicação das bonificações", margin_x, y, width - 2 * margin_x, height, font="Helvetica-Bold", size=10)
    y = _paragraphs(
        c,
        [
            "As bonificações geradas no âmbito do Programa de Prescritores serão acumuladas como créditos formativos dentro do sistema de benefícios da Sports Data Campus.",
            "Cada conversão em matrícula de um recomendado por O COLABORADOR gerará o valor correspondente detalhado no item 2.2, que poderá ser aplicado como bolsa de estudos, redução de custos de programas formativos, acesso a outros cursos ou redução proporcional de parcelas pendentes em mestrados em andamento.",
        ],
        margin_x,
        y,
        width,
        height,
    )
    y = draw_paragraph(c, "\n2.4 Registro e determinação das bonificações", margin_x, y, width - 2 * margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "Todas as matrículas convertidas, assim como as bonificações correspondentes, serão registradas no SIGP, que constituirá a única fonte válida para determinar:", margin_x, y, width - 2 * margin_x, height)
    y = draw_bullets(c, ["Atribuição do lead", "Conversão em matrícula", "Valor da bonificação aplicável", "Estado de reconhecimento e aplicação da bonificação."], margin_x, y, width - 2 * margin_x, height)

    y -= 10
    y = draw_paragraph(c, "TERCEIRA.- DEVENGO E LIQUIDAÇÃO DAS BONIFICAÇÕES", margin_x, y, width - 2 * margin_x, height, font="Helvetica-Bold")
    y = draw_paragraph(c, "\n3.1 Reconhecimento da bonificação", margin_x, y, width - 2 * margin_x, height, font="Helvetica-Bold", size=10)
    y = _paragraphs(
        c,
        [
            "A bonificação correspondente a uma matrícula convertida será reconhecida no momento em que o aluno indicado por O COLABORADOR tenha realizado o pagamento efetivo da matrícula do programa formativo correspondente e esse pagamento tenha sido recebido e validado por A EMPRESA conforme seus sistemas internos de cobrança.",
            "Para os efeitos deste acordo, entende-se por pagamento efetivo de matrícula aquele pagamento inicial ou confirmação de inscrição que permita formalizar a incorporação do aluno ao programa formativo correspondente.",
        ],
        margin_x,
        y,
        width,
        height,
    )
    y = draw_paragraph(c, "\n3.2 Validação das bonificações", margin_x, y, width - 2 * margin_x, height, font="Helvetica-Bold", size=10)
    y = _paragraphs(
        c,
        [
            "As bonificações geradas serão verificadas pelo departamento de Administração de A EMPRESA, que confirmará a validade da matrícula, a atribuição do lead e a inexistência de incidências financeiras associadas ao pagamento realizado pelo aluno.",
            "Uma vez validada a informação correspondente, a bonificação ficará registrada e disponível para aplicação dentro do sistema de benefícios do Programa de Prescritores.",
        ],
        margin_x,
        y,
        width,
        height,
    )
    y = draw_paragraph(c, "\n3.3 Condições para reconhecimento ou aplicação", margin_x, y, width - 2 * margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "A aplicação ou reconhecimento das bonificações estará sujeita às seguintes condições:", margin_x, y, width - 2 * margin_x, height)
    y = draw_bullets(c, ["Que a matrícula tenha sido validada conforme os sistemas de A EMPRESA;", "Que o pagamento do aluno não tenha sido objeto de devolução, estorno bancário ou incidência financeira;", "Que a atribuição do lead conste corretamente registrada no SIGP."], margin_x, y, width - 2 * margin_x, height)

    y -= 10
    y = draw_paragraph(c, "QUARTA.- GESTÃO DE CANCELAMENTOS E AJUSTES", margin_x, y, width - 2 * margin_x, height, font="Helvetica-Bold")
    y = draw_paragraph(c, "\n4.1 Hipóteses de regularização", margin_x, y, width - 2 * margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "As bonificações reconhecidas conforme a Cláusula Segunda poderão estar sujeitas a regularização nos seguintes casos:", margin_x, y, width - 2 * margin_x, height)
    y = draw_bullets(
        c,
        [
            "a) Quando o programa formativo não seja finalmente ministrado por causas organizacionais ou por não atingir o número mínimo de alunos.",
            "b) Quando o aluno exerça seu direito de desistência ou solicite baixa dentro dos prazos legais ou contratuais estabelecidos por A EMPRESA.",
            "c) Quando ocorra devolução total ou parcial do valor pago pelo aluno por qualquer causa devidamente justificada.",
            "d) Quando exista inadimplência, estorno bancário, chargeback ou qualquer incidência financeira que implique a anulação total ou parcial do pagamento que originou a bonificação.",
        ],
        margin_x,
        y,
        width - 2 * margin_x,
        height,
    )
    y = draw_paragraph(c, "\n4.2 Efeitos da regularização", margin_x, y, width - 2 * margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_bullets(
        c,
        [
            "A EMPRESA poderá anular ou ajustar a bonificação quando a matrícula que a originou incorra posteriormente em baixa, inadimplência, abandono ou qualquer incidência que implique a não continuidade do aluno no programa.",
            "Se a bonificação tiver sido aplicada total ou parcialmente, o valor correspondente poderá ser revertido, compensado ou ajustado dentro do sistema de benefícios do Programa de Prescritores.",
            "Quando a bonificação tenha sido utilizada para redução de parcelas ou custos de um programa em andamento, A EMPRESA poderá reimputar o valor correspondente a O COLABORADOR, que assumirá a diferença resultante.",
        ],
        margin_x,
        y,
        width - 2 * margin_x,
        height,
    )
    y = draw_paragraph(c, "\n4.3 Registro e transparência", margin_x, y, width - 2 * margin_x, height, font="Helvetica-Bold", size=10)
    y = _paragraphs(
        c,
        [
            "A EMPRESA manterá um registro interno das bonificações geradas, aplicadas ou ajustadas correspondentes a O COLABORADOR.",
            "Todas as incidências, cancelamentos, devoluções ou ajustes relacionados com matrículas convertidas serão registrados no SIGP, que constituirá a única fonte válida para determinar o estado de cada matrícula e das bonificações associadas.",
        ],
        margin_x,
        y,
        width,
        height,
    )

    y -= 10
    y = draw_paragraph(c, "QUINTA.- CONTROLE DE QUALIDADE E GESTÃO DE LEADS", margin_x, y, width - 2 * margin_x, height, font="Helvetica-Bold")
    y = draw_paragraph(c, "\n5.1 Definição de lead válido", margin_x, y, width - 2 * margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "Para os efeitos deste acordo, será considerado lead válido aquele prospecto que cumpra simultaneamente as seguintes condições:", margin_x, y, width - 2 * margin_x, height)
    y = draw_bullets(
        c,
        [
            "a) Forneça dados de contato completos, verdadeiros e verificáveis.",
            "b) Manifeste interesse real nos programas formativos de A EMPRESA.",
            "c) Cumpra os requisitos mínimos de acesso ao programa formativo correspondente.",
            "d) Não constitua informação duplicada, fraudulenta ou previamente registrada no SIGP por outro prescritor dentro do período de atribuição vigente.",
        ],
        margin_x,
        y,
        width - 2 * margin_x,
        height,
    )
    y = draw_paragraph(c, "A EMPRESA reserva-se o direito de validar a condição de lead válido conforme os critérios internos estabelecidos no SIGP.", margin_x, y, width - 2 * margin_x, height)
    y = draw_paragraph(c, "\n5.2 Registro e atribuição de leads", margin_x, y, width - 2 * margin_x, height, font="Helvetica-Bold", size=10)
    y = _paragraphs(
        c,
        [
            "Para que um lead possa gerar direito a bonificação, deverá ser registrado previamente no SIGP ou nas plataformas oficiais que A EMPRESA determine.",
            "A atribuição do lead corresponderá ao prescritor que o tenha registrado corretamente no SIGP em primeiro lugar. Essa atribuição permanecerá vigente por um período de seis (6) meses a partir da data de registro.",
            "Transcorrido esse prazo sem que tenha ocorrido matrícula convertida, o lead poderá ser trabalhado por outros prescritores, perdendo o primeiro a exclusividade sobre ele.",
        ],
        margin_x,
        y,
        width,
        height,
    )
    y = draw_paragraph(c, "\n5.3 Rastreabilidade e titularidade", margin_x, y, width - 2 * margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "A antiguidade, titularidade e estado dos leads serão determinados exclusivamente mediante o registro efetuado no SIGP, que dispõe de sistema de auditoria e registro interno de atividade.", margin_x, y, width - 2 * margin_x, height)
    y = draw_bullets(c, ["Titularidade do lead", "Data de registro", "Conversão em matrícula", "Reconhecimento e estado da bonificação correspondente."], margin_x, y, width - 2 * margin_x, height)
    y = draw_paragraph(c, "\n5.4 Territorialidade, exclusividade e controvérsias", margin_x, y, width - 2 * margin_x, height, font="Helvetica-Bold", size=10)
    y = _paragraphs(
        c,
        [
            "Dado que a atividade formativa de A EMPRESA se desenvolve principalmente em modalidade online, o presente acordo não estabelece exclusividade territorial.",
            "O COLABORADOR poderá promover os programas formativos em qualquer âmbito geográfico.",
            "Em caso de controvérsia sobre a titularidade de um lead ou sobre a atribuição de uma matrícula convertida, A EMPRESA resolverá a incidência tomando como referência a informação registrada no SIGP e os critérios internos de validação do Programa de Prescritores.",
        ],
        margin_x,
        y,
        width,
        height,
    )

    y -= 10
    y = draw_paragraph(c, "SEXTA.- PROPRIEDADE DA BASE DE DADOS E USO DA INFORMAÇÃO", margin_x, y, width - 2 * margin_x, height, font="Helvetica-Bold")
    y = _paragraphs(
        c,
        [
            "Todos os leads, dados de contato, informação comercial e qualquer outro dado gerado, captado ou gerido no âmbito do presente acordo serão propriedade exclusiva de A EMPRESA. Essa informação será gerida através do SIGP ou das plataformas oficiais que A EMPRESA determine.",
            "O COLABORADOR não adquire qualquer direito de propriedade, titularidade ou exploração sobre os dados gerados no âmbito deste acordo.",
            "O COLABORADOR compromete-se a utilizar essa informação exclusivamente para os fins estabelecidos neste acordo e conforme as instruções e diretrizes de A EMPRESA, respeitando em todo momento a legislação vigente de proteção de dados de cada território.",
            "É expressamente proibido que O COLABORADOR utilize os dados para fins distintos da promoção dos programas formativos de A EMPRESA, incorpore-os a bases de dados próprias ou de terceiros, ou comercialize produtos ou serviços alheios a A EMPRESA utilizando a informação obtida durante a vigência do acordo.",
            "Ao término do acordo, qualquer que seja a causa, O COLABORADOR deverá cessar imediatamente o uso dos dados, eliminar ou destruir qualquer cópia em seu poder e abster-se de contatar novamente os leads gerados, salvo autorização expressa e por escrito de A EMPRESA.",
        ],
        margin_x,
        y,
        width,
        height,
    )

    y -= 10
    y = draw_paragraph(c, "SÉTIMA.- OBRIGAÇÕES DAS PARTES", margin_x, y, width - 2 * margin_x, height, font="Helvetica-Bold")
    y = draw_paragraph(c, "\n7.1 Obrigações de A EMPRESA", margin_x, y, width - 2 * margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "A EMPRESA compromete-se a:", margin_x, y, width - 2 * margin_x, height)
    y = draw_bullets(
        c,
        [
            "Fornecer a O COLABORADOR informação comercial, materiais promocionais e documentação necessária para a correta promoção dos programas formativos.",
            "Facilitar o acesso ao SIGP como ferramenta oficial para o registro e acompanhamento de leads.",
            "Registrar e processar corretamente as matrículas convertidas e as bonificações geradas conforme este acordo.",
            "Reconhecer ou aplicar as bonificações correspondentes nos prazos e condições estabelecidos.",
            "Manter atualizado o sistema de bonificações vigente e comunicar por escrito qualquer modificação com antecedência mínima de trinta (30) dias corridos, salvo obrigação legal ou regulatória de aplicação imediata.",
        ],
        margin_x,
        y,
        width - 2 * margin_x,
        height,
    )
    y = draw_paragraph(c, "\n7.2 Obrigações de O COLABORADOR", margin_x, y, width - 2 * margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "O COLABORADOR compromete-se a:", margin_x, y, width - 2 * margin_x, height)
    y = draw_bullets(
        c,
        [
            "Promover, recomendar e divulgar os programas formativos de A EMPRESA de forma profissional, ética e conforme a imagem, valores e diretrizes comerciais da Sports Data Campus.",
            "Registrar todos os leads exclusivamente através do SIGP ou dos canais oficiais estabelecidos por A EMPRESA.",
            "Cumprir a normativa vigente em matéria de proteção de dados, comunicações comerciais e qualquer outra regulação aplicável à sua atividade.",
            "Não oferecer condições econômicas, descontos, bolsas, garantias ou promessas que não estejam expressamente autorizadas por A EMPRESA.",
            "Informar A EMPRESA sobre qualquer incidência relevante relacionada com leads ou alunos geridos.",
            "Atuar sempre como colaborador independente, sem representação legal nem capacidade para obrigar contratualmente A EMPRESA perante terceiros.",
        ],
        margin_x,
        y,
        width - 2 * margin_x,
        height,
    )

    y -= 10
    y = draw_paragraph(c, "OITAVA.- DURAÇÃO E RESOLUÇÃO DO ACORDO", margin_x, y, width - 2 * margin_x, height, font="Helvetica-Bold")
    y = _paragraphs(
        c,
        [
            "O presente acordo terá duração inicial de um (1) ano a contar da data de sua assinatura. Finalizado esse período, será renovado automaticamente por períodos sucessivos de um (1) ano, salvo se qualquer das partes comunicar por escrito sua vontade de não renovação com antecedência mínima de trinta (30) dias corridos antes do vencimento.",
            "O acordo poderá ser resolvido antecipadamente por incumprimento grave de qualquer obrigação, por mútuo acordo formalizado por escrito ou por decisão unilateral de qualquer das partes mediante aviso prévio escrito com pelo menos trinta (30) dias corridos de antecedência.",
            "Considera-se que O COLABORADOR está em situação de inatividade quando não tenha registrado nenhum lead válido no SIGP durante um período continuado de três (3) meses. Nesses casos, A EMPRESA poderá considerar finalizada a participação de O COLABORADOR no Programa de Prescritores ou convidá-lo a aderir às condições vigentes do programa.",
            "Em caso de resolução, O COLABORADOR deixará de ter direito a registrar novos leads desde a data efetiva de finalização. Serão liquidadas exclusivamente as bonificações reconhecidas conforme este acordo e não sujeitas a regularização. As obrigações de confidencialidade, proteção de dados e uso da informação permanecerão vigentes após a finalização.",
        ],
        margin_x,
        y,
        width,
        height,
    )

    y -= 10
    y = draw_paragraph(c, "NONA.- CONFIDENCIALIDADE", margin_x, y, width - 2 * margin_x, height, font="Helvetica-Bold")
    y = _paragraphs(
        c,
        [
            "O COLABORADOR compromete-se a manter a mais estrita confidencialidade sobre toda informação a que tenha acesso em consequência da execução deste acordo.",
            "Considera-se informação confidencial toda informação técnica, comercial, estratégica, financeira ou de qualquer outra natureza pertencente a A EMPRESA, incluindo informação comercial ou estratégica da Sports Data Campus, dados econômicos, financeiros ou de faturamento, condições comerciais ou contratuais, informação relativa a alunos, leads ou clientes, e funcionamento interno do SIGP ou de outras ferramentas tecnológicas utilizadas por A EMPRESA.",
            "O COLABORADOR não divulgará informação confidencial a terceiros sem autorização prévia e por escrito de A EMPRESA, não a utilizará para fins distintos dos derivados da execução deste acordo e adotará as medidas necessárias para evitar acesso não autorizado.",
            "A obrigação de confidencialidade permanecerá vigente durante a duração do acordo e continuará em vigor por um período mínimo de cinco (5) anos após sua finalização, qualquer que seja a causa.",
        ],
        margin_x,
        y,
        width,
        height,
    )

    y -= 10
    y = draw_paragraph(c, "DÉCIMA.- PROTEÇÃO DE DADOS", margin_x, y, width - 2 * margin_x, height, font="Helvetica-Bold")
    y = _paragraphs(
        c,
        [
            "As partes comprometem-se a cumprir o Regulamento (UE) 2016/679 do Parlamento Europeu e do Conselho, de 27 de abril de 2016 (RGPD), a Lei Orgânica 3/2018 de Proteção de Dados Pessoais e garantia dos direitos digitais (LOPDGDD) e demais normativa vigente em matéria de proteção de dados pessoais.",
            "O COLABORADOR tratará os dados pessoais a que tenha acesso exclusivamente para a correta execução deste acordo e conforme as instruções de A EMPRESA.",
        ],
        margin_x,
        y,
        width,
        height,
    )
    y = draw_bullets(
        c,
        [
            "Não utilizar os dados pessoais para fins próprios nem distintos dos previstos neste acordo.",
            "Não ceder dados pessoais a terceiros sem autorização prévia e expressa de A EMPRESA, salvo obrigação legal.",
            "Aplicar medidas técnicas e organizacionais adequadas para garantir a segurança e confidencialidade dos dados pessoais tratados.",
            "Informar imediatamente A EMPRESA em caso de incidente de segurança, acesso não autorizado, perda ou violação que afete dados pessoais vinculados ao acordo.",
            "Ao término do acordo, eliminar ou devolver a A EMPRESA todos os dados pessoais a que tenha tido acesso e abster-se de conservar cópias, salvo obrigação legal de conservação.",
        ],
        margin_x,
        y,
        width - 2 * margin_x,
        height,
    )

    y -= 10
    y = draw_paragraph(c, "DÉCIMA PRIMEIRA.- SUBSTITUIÇÃO DE ACORDOS ANTERIORES E TRANSIÇÃO", margin_x, y, width - 2 * margin_x, height, font="Helvetica-Bold")
    y = _paragraphs(
        c,
        [
            "O presente acordo substitui e deixa sem efeito qualquer acordo, convênio ou entendimento prévio existente entre as partes relativo à participação em programas de prescrição ou colaboração comercial vinculados aos programas formativos de A EMPRESA, seja de natureza verbal ou escrita.",
            "Em caso de contradição entre o presente acordo e qualquer documento anterior assinado entre as partes sobre o mesmo objeto, prevalecerá o disposto neste acordo.",
            "Nos casos em que O COLABORADOR tenha gerado atividade prévia dentro do Programa de Prescritores antes da assinatura deste acordo, A EMPRESA poderá manter temporariamente as condições anteriormente aplicáveis até sua revisão ou adaptação às condições vigentes do programa.",
            "Considera-se que um prescritor está em situação de inatividade quando não tenha registrado nenhum lead válido no SIGP durante um período continuado de três (3) meses. Nesses casos, A EMPRESA poderá considerar extinto o acordo anterior e oferecer ao prescritor a adesão ao modelo vigente.",
        ],
        margin_x,
        y,
        width,
        height,
    )

    y -= 10
    y = draw_paragraph(c, "DÉCIMA SEGUNDA.- LEGISLAÇÃO APLICÁVEL E JURISDIÇÃO", margin_x, y, width - 2 * margin_x, height, font="Helvetica-Bold")
    y = _paragraphs(
        c,
        [
            "O presente acordo tem natureza mercantil e será regido e interpretado conforme a legislação espanhola vigente.",
            "Para a resolução de qualquer controvérsia, discrepância ou conflito que possa derivar da interpretação, execução ou validade deste acordo, as partes submetem-se expressamente à jurisdição dos Juízos e Tribunais de Valladolid, Espanha, com renúncia expressa a qualquer outro foro que pudesse corresponder-lhes.",
        ],
        margin_x,
        y,
        width,
        height,
    )

    draw_signatures(c, width, height, datos, y)
